from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class MealType(enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    food_entries: Mapped[list["FoodEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    daily_stats: Mapped[list["DailyStats"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    weight_logs: Mapped[list["WeightLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class FoodEntry(Base):
    __tablename__ = "food_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Meal info
    meal_type: Mapped[MealType] = mapped_column(SQLEnum(MealType))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Nutrition data (КБЖУ)
    calories: Mapped[float] = mapped_column(Float)
    protein: Mapped[float] = mapped_column(Float)  # белки
    fats: Mapped[float] = mapped_column(Float)  # жиры
    carbs: Mapped[float] = mapped_column(Float)  # углеводы

    # Source tracking
    source_type: Mapped[str] = mapped_column(String(50))  # 'photo', 'label', 'text'
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="food_entries")


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Calories consumed (from food entries)
    total_calories: Mapped[float] = mapped_column(Float, default=0)
    total_protein: Mapped[float] = mapped_column(Float, default=0)
    total_fats: Mapped[float] = mapped_column(Float, default=0)
    total_carbs: Mapped[float] = mapped_column(Float, default=0)

    # Calories burned (from wearables)
    calories_burned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Surplus calculation
    calorie_surplus: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="daily_stats")


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    weight: Mapped[float] = mapped_column(Float)  # in kg
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="weight_logs")
