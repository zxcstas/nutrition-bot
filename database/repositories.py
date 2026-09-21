from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, FoodEntry, DailyStats, WeightLog, MealType


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Get existing user or create new one"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, username=username)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user


class FoodEntryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_entry(
        self,
        user_id: int,
        meal_type: MealType,
        description: str,
        calories: float,
        protein: float,
        fats: float,
        carbs: float,
        source_type: str,
        photo_path: Optional[str] = None,
    ) -> FoodEntry:
        """Create new food entry"""
        entry = FoodEntry(
            user_id=user_id,
            meal_type=meal_type,
            description=description,
            calories=calories,
            protein=protein,
            fats=fats,
            carbs=carbs,
            source_type=source_type,
            photo_path=photo_path,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get_entries_by_date(self, user_id: int, target_date: date) -> List[FoodEntry]:
        """Get all food entries for specific date"""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        result = await self.session.execute(
            select(FoodEntry)
            .where(
                and_(
                    FoodEntry.user_id == user_id,
                    FoodEntry.created_at >= start,
                    FoodEntry.created_at <= end,
                )
            )
            .order_by(FoodEntry.created_at)
        )
        return list(result.scalars().all())


class DailyStatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_stats(self, user_id: int, target_date: date) -> DailyStats:
        """Get or create daily stats for specific date"""
        date_start = datetime.combine(target_date, datetime.min.time())

        result = await self.session.execute(
            select(DailyStats).where(
                and_(
                    DailyStats.user_id == user_id,
                    func.date(DailyStats.date) == target_date,
                )
            )
        )
        stats = result.scalar_one_or_none()

        if not stats:
            stats = DailyStats(user_id=user_id, date=date_start)
            self.session.add(stats)
            await self.session.commit()
            await self.session.refresh(stats)

        return stats

    async def update_nutrition_totals(
        self,
        user_id: int,
        target_date: date,
        total_calories: float,
        total_protein: float,
        total_fats: float,
        total_carbs: float,
    ):
        """Update daily nutrition totals"""
        stats = await self.get_or_create_stats(user_id, target_date)
        stats.total_calories = total_calories
        stats.total_protein = total_protein
        stats.total_fats = total_fats
        stats.total_carbs = total_carbs

        # Recalculate surplus if calories_burned is set
        if stats.calories_burned is not None:
            stats.calorie_surplus = total_calories - stats.calories_burned

        await self.session.commit()

    async def update_calories_burned(self, user_id: int, target_date: date, calories_burned: float):
        """Update calories burned and recalculate surplus"""
        stats = await self.get_or_create_stats(user_id, target_date)
        stats.calories_burned = calories_burned
        stats.calorie_surplus = stats.total_calories - calories_burned
        await self.session.commit()


class WeightLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_weight(self, user_id: int, weight: float) -> WeightLog:
        """Log user weight"""
        log = WeightLog(user_id=user_id, weight=weight)
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_latest_weight(self, user_id: int) -> Optional[WeightLog]:
        """Get most recent weight log"""
        result = await self.session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user_id)
            .order_by(WeightLog.logged_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
