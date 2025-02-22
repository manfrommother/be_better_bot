from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum
from src.models.base import BaseModel
from enum import Enum as PyEnum

class CategoryType(str, PyEnum):
    """Типы категорий расходов/доходов"""
    INCOME = "income"
    EXPENSE = "expense"

class Category(BaseModel):
    """Модель категории расходов/доходов"""
    __tablename__ = 'categories'
    
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'income' или 'expense'
    user_id = Column(Integer, nullable=False)

class Transaction(BaseModel):
    """Модель транзакции (расход/доход)"""
    __tablename__ = 'transactions'
    
    amount = Column(Numeric(10, 2), nullable=False)  # Сумма с двумя знаками после запятой
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    description = Column(String(200))