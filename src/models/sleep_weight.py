from sqlalchemy import Column, DateTime, Integer, Numeric
from src.models.base import BaseModel

class SleepRecord(BaseModel):
    '''Модель записи сна'''
    __tablename__ = 'sleep_records'

    sleep_time = Column(DateTime, nullable=False)
    wake_time = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False)


class WeightRecord(BaseModel):
    '''Модель записи веса'''
    __tablename__ = 'weight_records'

    weight = Column(Numeric(4, 1), nullable=False)
    user_id = Column(Integer, nullable=False)
    record_date = Column(DateTime, nullable=False)