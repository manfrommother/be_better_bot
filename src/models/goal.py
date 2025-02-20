from base import BaseModel
from sqlalchemy import Column, Integer, String, Numeric, Enum, DateTime
import enum


class GoalStatus(enum.Enum):
    '''Статус целей'''
    ACTIVE = 'active'
    COMPLETED = 'completed'
    FAILED = 'failed'

class Goal(BaseModel):
    '''Модель целей для пользователя'''
    __tablename__ = 'goals'

    title = Column(String(200), nullable=False)
    description = Column(String(500))
    target_value = Column(Numeric(10, 2))
    current_value = Column(Numeric(10, 2))
    deadline = Column(DateTime)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    user_id = Column(Integer, nullable=False)
    

