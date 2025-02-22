from enum import Enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime
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
   goal_type = Column(String(20), nullable=False)  # Просто используем String
   target_value = Column(Numeric(10, 2), nullable=False)
   current_value = Column(Numeric(10, 2), nullable=False)
   start_value = Column(Numeric(10, 2), nullable=False)
   deadline = Column(DateTime, nullable=False)
   status = Column(String(20), default=GoalStatus.ACTIVE.value)  # И здесь тоже String
   user_id = Column(Integer, nullable=False)

   @property
   def goal_type_enum(self) -> GoalType:
       """Получение типа цели как enum"""
       return GoalType(self.goal_type)

   @goal_type_enum.setter
   def goal_type_enum(self, value: GoalType):
       """Установка типа цели из enum"""
       self.goal_type = value.value

   @property
   def status_enum(self) -> GoalStatus:
       """Получение статуса как enum"""
       return GoalStatus(self.status)

   @status_enum.setter
   def status_enum(self, value: GoalStatus):
       """Установка статуса из enum"""
       self.status = value.value
    

