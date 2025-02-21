from decimal import Decimal
from models.base import BaseModel
from sqlalchemy import Column, Integer, Numeric, Enum, Boolean
import enum

class RoundingStep(enum.Enum):
    """Шаг округления для накопительного счёта"""
    STEP_10 = 10
    STEP_50 = 50
    STEP_100 = 100

class UserSettings(BaseModel):
    """Модель настроек пользователя"""
    __tablename__ = 'user_settings'
    
    user_id = Column(Integer, unique=True, nullable=False)
    rounding_step = Column(Enum(RoundingStep), default=RoundingStep.STEP_10)
    savings_enabled = Column(Boolean, default=True)

class SavingsAccount(BaseModel):
    """Модель накопительного счёта"""
    __tablename__ = 'savings_accounts'
    
    user_id = Column(Integer, unique=True, nullable=False)
    balance = Column(Numeric(10, 2), default=0)