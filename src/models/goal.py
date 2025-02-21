from base import BaseModel
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum
import enum


class GoalStatus(enum.Enum):
    '''Статус целей'''
    ACTIVE = 'active'
    COMPLETED = 'completed'
    FAILED = 'failed'


class GoalType(Enum):
    '''Типы целей'''
    SAVINGS = 'savings'
    WEIGHT = 'weight'


class Goal(BaseModel):
    """Модель целей пользователя"""
    __tablename__ = 'goals'
    
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    goal_type = Column(Enum(GoalType), nullable=False)
    target_value = Column(Numeric(10, 2), nullable=False)  # Целевое значение (деньги или вес)
    current_value = Column(Numeric(10, 2), nullable=False) # Текущее значение
    start_value = Column(Numeric(10, 2), nullable=False)   # Начальное значение
    deadline = Column(DateTime, nullable=False)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    user_id = Column(Integer, nullable=False)
    

