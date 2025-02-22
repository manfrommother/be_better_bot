from sqlalchemy import Column, String, DateTime, Boolean, Integer
from src.models.base import BaseModel


class Reminder(BaseModel):
    '''Модель напоминания'''
    __tablename__ = 'reminders'

    text = Column(String(500), nullable=False)
    remind_at = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=False)

