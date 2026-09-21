from datetime import date, datetime
from typing import List, Dict
from database import FoodEntry, DailyStats, MealType
from database.repositories import FoodEntryRepository, DailyStatsRepository
import logging

logger = logging.getLogger(__name__)


class StatisticsService:
    """Service for calculating and formatting statistics"""

    @staticmethod
    async def recalculate_daily_totals(
        user_id: int,
        target_date: date,
        food_repo: FoodEntryRepository,
        stats_repo: DailyStatsRepository,
    ):
        """Recalculate daily nutrition totals after new entry"""
        entries = await food_repo.get_entries_by_date(user_id, target_date)

        total_calories = sum(e.calories for e in entries)
        total_protein = sum(e.protein for e in entries)
        total_fats = sum(e.fats for e in entries)
        total_carbs = sum(e.carbs for e in entries)

        await stats_repo.update_nutrition_totals(
            user_id=user_id,
            target_date=target_date,
            total_calories=total_calories,
            total_protein=total_protein,
            total_fats=total_fats,
            total_carbs=total_carbs,
        )

    @staticmethod
    def format_daily_summary(entries: List[FoodEntry], stats: DailyStats) -> str:
        """Format daily summary message"""
        if not entries:
            return "📊 Сегодня пока нет записей о питании."

        # Group by meal type
        meals_by_type = {
            MealType.BREAKFAST: [],
            MealType.LUNCH: [],
            MealType.DINNER: [],
            MealType.SNACK: [],
        }

        for entry in entries:
            meals_by_type[entry.meal_type].append(entry)

        # Build message
        message = "📊 <b>Сводка за сегодня</b>\n\n"

        # Meal breakdown
        meal_names = {
            MealType.BREAKFAST: "🌅 Завтрак",
            MealType.LUNCH: "🌞 Обед",
            MealType.DINNER: "🌙 Ужин",
            MealType.SNACK: "🍎 Перекусы",
        }

        for meal_type, meal_entries in meals_by_type.items():
            if not meal_entries:
                continue

            meal_calories = sum(e.calories for e in meal_entries)
            message += f"\n{meal_names[meal_type]} ({meal_calories:.0f} ккал):\n"

            for entry in meal_entries:
                time = entry.created_at.strftime("%H:%M")
                message += f"  • {time} - {entry.description} ({entry.calories:.0f} ккал)\n"

        # Totals
        message += f"\n<b>Итого потреблено:</b>\n"
        message += f"🔥 Калории: {stats.total_calories:.0f} ккал\n"
        message += f"🥩 Белки: {stats.total_protein:.1f}г\n"
        message += f"🧈 Жиры: {stats.total_fats:.1f}г\n"
        message += f"🍞 Углеводы: {stats.total_carbs:.1f}г\n"

        # Calories burned and surplus
        if stats.calories_burned is not None:
            message += f"\n🏃 Потрачено калорий: {stats.calories_burned:.0f} ккал\n"

            if stats.calorie_surplus is not None:
                surplus_emoji = "📈" if stats.calorie_surplus > 0 else "📉"
                surplus_text = "Профицит" if stats.calorie_surplus > 0 else "Дефицит"
                message += f"{surplus_emoji} <b>{surplus_text}: {abs(stats.calorie_surplus):.0f} ккал</b>\n"
        else:
            message += f"\n💡 Добавь расход калорий командой /burned чтобы увидеть профицит\n"

        return message

    @staticmethod
    def format_entry_confirmation(entry: FoodEntry) -> str:
        """Format confirmation message for new entry"""
        meal_emoji = {
            MealType.BREAKFAST: "🌅",
            MealType.LUNCH: "🌞",
            MealType.DINNER: "🌙",
            MealType.SNACK: "🍎",
        }

        meal_names = {
            MealType.BREAKFAST: "Завтрак",
            MealType.LUNCH: "Обед",
            MealType.DINNER: "Ужин",
            MealType.SNACK: "Перекус",
        }

        emoji = meal_emoji.get(entry.meal_type, "🍽")
        meal_name = meal_names.get(entry.meal_type, "Прием пищи")

        message = f"✅ <b>{meal_name} добавлен!</b>\n\n"
        message += f"{emoji} {entry.description}\n\n"
        message += f"🔥 Калории: {entry.calories:.0f} ккал\n"
        message += f"🥩 Белки: {entry.protein:.1f}г\n"
        message += f"🧈 Жиры: {entry.fats:.1f}г\n"
        message += f"🍞 Углеводы: {entry.carbs:.1f}г\n"

        return message
