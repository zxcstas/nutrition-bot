from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date
import io
import logging

from database import async_session_maker, FoodEntryRepository, DailyStatsRepository, MealType
from services import tokenclub_api, NutritionParser, StatisticsService

logger = logging.getLogger(__name__)

router = Router()


class FoodInputStates(StatesGroup):
    waiting_for_meal_type = State()


@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Handle photo input (food or nutrition label)"""
    await message.answer("🔍 Анализирую фото...")

    try:
        # Get the largest photo
        photo = message.photo[-1]
        photo_file = await message.bot.get_file(photo.file_id)
        photo_data = await message.bot.download_file(photo_file.file_path)

        # Convert to bytes
        photo_bytes = photo_data.read()

        # Try to determine if it's a label or food photo
        # For now, we'll ask the user or use Vision API for both
        # User can add caption "этикетка" to indicate it's a label
        is_label = message.caption and "этикетка" in message.caption.lower()

        if is_label:
            # Analyze as nutrition label
            result = await tokenclub_api.analyze_nutrition_label(photo_bytes)
            nutrition_info = NutritionParser.parse_label_response(result) if result else None
        else:
            # Analyze as food photo
            result = await tokenclub_api.analyze_food_image(photo_bytes)
            nutrition_info = NutritionParser.parse_vision_response(result) if result else None

        if not nutrition_info:
            await message.answer(
                "❌ Не удалось распознать питательную ценность.\n"
                "Попробуй написать описание текстом или пришли фото этикетки с подписью 'этикетка'"
            )
            return

        # Store nutrition info in state
        await state.update_data(
            nutrition_info=nutrition_info,
            source_type="label" if is_label else "photo",
            photo_file_id=photo.file_id,
        )

        # Show recognized info and ask for meal type
        confirmation_text = f"✅ <b>Распознано:</b>\n\n"
        confirmation_text += f"{nutrition_info.description}\n\n"
        confirmation_text += f"🔥 Калории: {nutrition_info.calories:.0f} ккал\n"
        confirmation_text += f"🥩 Белки: {nutrition_info.protein:.1f}г\n"
        confirmation_text += f"🧈 Жиры: {nutrition_info.fats:.1f}г\n"
        confirmation_text += f"🍞 Углеводы: {nutrition_info.carbs:.1f}г\n"

        if nutrition_info.confidence == "low":
            confirmation_text += f"\n⚠️ Уверенность низкая, данные приблизительные\n"

        confirmation_text += f"\n<b>К какому приему пищи отнести?</b>"

        # Meal type keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 Завтрак", callback_data="meal:breakfast"),
                InlineKeyboardButton(text="🌞 Обед", callback_data="meal:lunch"),
            ],
            [
                InlineKeyboardButton(text="🌙 Ужин", callback_data="meal:dinner"),
                InlineKeyboardButton(text="🍎 Перекус", callback_data="meal:snack"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="meal:cancel"),
            ],
        ])

        await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(FoodInputStates.waiting_for_meal_type)

    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await message.answer("❌ Произошла ошибка при обработке фото")


@router.message(F.text & ~F.text.startswith('/'))
async def handle_text_food(message: Message, state: FSMContext):
    """Handle text food description"""
    await message.answer("🔍 Анализирую описание...")

    try:
        # Parse text using LLM
        result = await tokenclub_api.parse_text_food_description(message.text)
        nutrition_info = NutritionParser.parse_llm_response(result) if result else None

        if not nutrition_info:
            await message.answer(
                "❌ Не удалось распознать еду из описания.\n"
                "Попробуй описать подробнее или пришли фото"
            )
            return

        # Store nutrition info
        await state.update_data(
            nutrition_info=nutrition_info,
            source_type="text",
            original_text=message.text,
        )

        # Show recognized info and ask for meal type
        confirmation_text = f"✅ <b>Распознано:</b>\n\n"
        confirmation_text += f"{nutrition_info.description}\n\n"
        confirmation_text += f"🔥 Калории: {nutrition_info.calories:.0f} ккал\n"
        confirmation_text += f"🥩 Белки: {nutrition_info.protein:.1f}г\n"
        confirmation_text += f"🧈 Жиры: {nutrition_info.fats:.1f}г\n"
        confirmation_text += f"🍞 Углеводы: {nutrition_info.carbs:.1f}г\n"

        if nutrition_info.confidence == "low":
            confirmation_text += f"\n⚠️ Уверенность низкая, данные приблизительные\n"

        confirmation_text += f"\n<b>К какому приему пищи отнести?</b>"

        # Meal type keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 Завтрак", callback_data="meal:breakfast"),
                InlineKeyboardButton(text="🌞 Обед", callback_data="meal:lunch"),
            ],
            [
                InlineKeyboardButton(text="🌙 Ужин", callback_data="meal:dinner"),
                InlineKeyboardButton(text="🍎 Перекус", callback_data="meal:snack"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="meal:cancel"),
            ],
        ])

        await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(FoodInputStates.waiting_for_meal_type)

    except Exception as e:
        logger.error(f"Error handling text food: {e}")
        await message.answer("❌ Произошла ошибка при обработке текста")


@router.callback_query(F.data.startswith("meal:"))
async def handle_meal_type_selection(callback: CallbackQuery, state: FSMContext):
    """Handle meal type selection"""
    await callback.answer()

    meal_type_str = callback.data.split(":")[1]

    if meal_type_str == "cancel":
        await callback.message.edit_text("❌ Отменено")
        await state.clear()
        return

    # Map callback data to MealType enum
    meal_type_map = {
        "breakfast": MealType.BREAKFAST,
        "lunch": MealType.LUNCH,
        "dinner": MealType.DINNER,
        "snack": MealType.SNACK,
    }

    meal_type = meal_type_map.get(meal_type_str)
    if not meal_type:
        await callback.message.edit_text("❌ Ошибка выбора приема пищи")
        await state.clear()
        return

    # Get stored nutrition info
    data = await state.get_data()
    nutrition_info = data.get("nutrition_info")
    source_type = data.get("source_type")

    if not nutrition_info:
        await callback.message.edit_text("❌ Ошибка: данные о еде не найдены")
        await state.clear()
        return

    try:
        # Save to database
        async with async_session_maker() as session:
            food_repo = FoodEntryRepository(session)
            stats_repo = DailyStatsRepository(session)

            # Create food entry
            entry = await food_repo.create_entry(
                user_id=callback.from_user.id,
                meal_type=meal_type,
                description=nutrition_info.description,
                calories=nutrition_info.calories,
                protein=nutrition_info.protein,
                fats=nutrition_info.fats,
                carbs=nutrition_info.carbs,
                source_type=source_type,
                photo_path=data.get("photo_file_id"),
            )

            # Recalculate daily totals
            await StatisticsService.recalculate_daily_totals(
                callback.from_user.id,
                date.today(),
                food_repo,
                stats_repo,
            )

        # Send confirmation
        confirmation = StatisticsService.format_entry_confirmation(entry)
        await callback.message.edit_text(confirmation, parse_mode="HTML")

        # Clear state
        await state.clear()

    except Exception as e:
        logger.error(f"Error saving food entry: {e}")
        await callback.message.edit_text("❌ Ошибка при сохранении записи")
        await state.clear()
