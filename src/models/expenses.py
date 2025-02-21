from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum
from base import BaseModel
import enum


class CategoryType(enum.Enum):
    '''Типы расходов/доходов'''
    INCOME = 'income'
    EXPENSE = 'expense'

class Category(BaseModel):
    '''Модель категории расходов/доходов'''
    __tablename__ = 'categories'

    name = Column(String(100), nullable=False)
    type = Column(Enum(CategoryType), nullable=False)
    user_id = Column(Integer, nullable=False)

class Transaction(BaseModel):
    '''Модель транзакции (расход/доход)'''
    __tablename__ = 'transactions'

    amount = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    description = Column(String(200))
    