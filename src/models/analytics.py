from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from enum import Enum
from datetime import datetime
from src.models.base import BaseModel
import json

class ActivityType(Enum):
    """
    Типы действий пользователя для аналитики
    """
    EXPENSE_ADDED = "expense_added"          
    INCOME_ADDED = "income_added"            
    WEIGHT_RECORDED = "weight_recorded"      
    SLEEP_STARTED = "sleep_started"          
    SLEEP_ENDED = "sleep_ended"              
    GOAL_CREATED = "goal_created"            
    GOAL_COMPLETED = "goal_completed"        
    REPORT_VIEWED = "report_viewed"          
    SETTINGS_CHANGED = "settings_changed"    

class UserActivity(BaseModel):
    """
    Модель для отслеживания активности пользователя
    """
    __tablename__ = 'user_activities'

    user_id = Column(Integer, nullable=False, index=True)
    action = Column(SQLEnum(ActivityType), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(String(500))  # JSON с дополнительной информацией