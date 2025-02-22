from sqlalchemy import Column, Integer, DateTime, String, Numeric
from src.models.base import BaseModel


class Exercise(BaseModel):
    '''Модель упражнения'''
    __tablename__ = 'exercises'

    name = Column(String(100), nullable=False)
    weight = Column(Numeric(5, 2))
    reps = Column(Integer)
    sets = Column(Integer)
    user_id = Column(Integer, nullable=False)
    workout_date = Column(DateTime, nullable=False)

