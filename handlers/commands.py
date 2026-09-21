from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import date
from database import async_session_maker, DailyStatsRepository, FoodEntryRepository
from services import StatisticsService

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show daily statistics"""
    async with async_session_maker() as session:
        food_repo = FoodEntryRepository(session)
        stats_repo = DailyStatsRepository(session)

        today = date.today()
        entries = await food_repo.get_entries_by_date(message.from_user.id, today)
        stats = await stats_repo.get_or_create_stats(message.from_user.id, today)

        summary = StatisticsService.format_daily_summary(entries, stats)
        await message.answer(summary, parse_mode="HTML")


@router.message(Command("burned"))
async def cmd_burned(message: Message):
    """Log calories burned"""
    try:
        # Extract calories from command
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer(
                "❌ Укажи количество потраченных калорий.\n"
                "Пример: /burned 2500"
            )
            return

        calories_burned = float(args[1])

        if calories_burned <= 0:
            await message.answer("❌ Количество калорий должно быть положительным числом")
            return

        async with async_session_maker() as session:
            stats_repo = DailyStatsRepository(session)
            today = date.today()

            await stats_repo.update_calories_burned(
                message.from_user.id,
                today,
                calories_burned
            )

            # Get updated stats
            stats = await stats_repo.get_or_create_stats(message.from_user.id, today)

            response = f"✅ <b>Расход калорий обновлен</b>\n\n"
            response += f"🏃 Потрачено: {calories_burned:.0f} ккал\n"
            response += f"🍽 Потреблено: {stats.total_calories:.0f} ккал\n"

            if stats.calorie_surplus is not None:
                if stats.calorie_surplus > 0:
                    response += f"\n📈 <b>Профицит: +{stats.calorie_surplus:.0f} ккал</b>"
                else:
                    response += f"\n📉 <b>Дефицит: {stats.calorie_surplus:.0f} ккал</b>"

            await message.answer(response, parse_mode="HTML")

    except ValueError:
        await message.answer("❌ Неверный формат. Укажи число.\nПример: /burned 2500")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("weight"))
async def cmd_weight(message: Message):
    """Log body weight"""
    try:
        from database import WeightLogRepository

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer(
                "❌ Укажи свой вес.\n"
                "Пример: /weight 75.5"
            )
            return

        weight = float(args[1])

        if weight <= 0 or weight > 300:
            await message.answer("❌ Укажи корректный вес (от 0 до 300 кг)")
            return

        async with async_session_maker() as session:
            weight_repo = WeightLogRepository(session)
            await weight_repo.log_weight(message.from_user.id, weight)

            # Get previous weight for comparison
            logs = await session.execute(
                "SELECT weight FROM weight_logs WHERE user_id = ? ORDER BY logged_at DESC LIMIT 2",
                [message.from_user.id]
            )

            response = f"✅ <b>Вес записан</b>\n\n⚖️ {weight} кг"
            await message.answer(response, parse_mode="HTML")

    except ValueError:
        await message.answer("❌ Неверный формат. Укажи число.\nПример: /weight 75.5")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
