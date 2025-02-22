from enum import Enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum as SQLEnum
from src.models.base import BaseModel

class GoalType(str, Enum):
    """Типы целей пользователя"""
    SAVINGS = "savings"  # Цель по накоплению денег
    WEIGHT = "weight"   # Цель по весу

class GoalStatus(str, Enum):
    """Статусы целей"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class Goal(BaseModel):
    """Модель целей пользователя"""
    __tablename__ = 'goals'
    
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    goal_type = Column(SQLEnum("goal_type", ["savings", "weight"]), nullable=False)
    target_value = Column(Numeric(10, 2), nullable=False)  # Целевое значение (деньги или вес)
    current_value = Column(Numeric(10, 2), nullable=False) # Текущее значение
    start_value = Column(Numeric(10, 2), nullable=False)   # Начальное значение
    deadline = Column(DateTime, nullable=False)
    status = Column(SQLEnum("goal_status", ["active", "completed", "failed"]), default="active")  # Исправлено
    user_id = Column(Integer, nullable=False)
    

