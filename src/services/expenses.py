from decimal import Decimal
from sqlalchemy import Transaction
import math

from models.savings import RoundingStep, UserSettings, SavingsAccount


class ExpensesService:
    """Сервис для работы с расходами и доходами"""
    def __init__(self, db_service):
        self.db = db_service

    def calculate_rounding_amount(self, amount: Decimal, rounding_step: RoundingStep) -> tuple[Decimal, Decimal]:
        """
        Рассчитывает сумму округления для накопительного счёта
        
        :param amount: Исходная сумма транзакции
        :param rounding_step: Шаг округления (10, 50 или 100)
        :return: (округленная_сумма, сумма_на_накопительный_счет)
        """
        step = rounding_step.value
        # Находим следующее число, которое делится на шаг округления
        rounded_up = Decimal(str(math.ceil(float(amount) / step) * step))
        savings_amount = rounded_up - amount
        return rounded_up, savings_amount

    async def create_transaction(
        self,
        user_id: int,
        category_id: int,
        amount: Decimal,
        description: str = None
    ) -> tuple[Transaction, Decimal]:
        """
        Создание новой транзакции с округлением на накопительный счёт
        
        :return: (транзакция, сумма_округления)
        """
        with self.db.get_session() as session:
            # Получаем настройки пользователя
            settings = session.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = UserSettings(user_id=user_id)
                session.add(settings)
            
            total_amount, savings_amount = self.calculate_rounding_amount(
                amount,
                settings.rounding_step
            )
            
            # Создаем транзакцию
            transaction = Transaction(
                user_id=user_id,
                category_id=category_id,
                amount=amount,  # Сохраняем реальную сумму траты
                description=description
            )
            session.add(transaction)
            
            # Если включено округление, добавляем на накопительный счёт
            if settings.savings_enabled and savings_amount > 0:
                savings_account = session.query(SavingsAccount).filter(
                    SavingsAccount.user_id == user_id
                ).first()
                
                if not savings_account:
                    savings_account = SavingsAccount(user_id=user_id)
                    session.add(savings_account)
                
                savings_account.balance += savings_amount
                
                # Если есть активная цель по накоплению, обновляем её
                await self._update_savings_goals(user_id, savings_amount)
            
            return transaction, savings_amount

    async def get_savings_balance(self, user_id: int) -> Decimal:
        """Получение баланса накопительного счёта"""
        with self.db.get_session() as session:
            account = session.query(SavingsAccount).filter(
                SavingsAccount.user_id == user_id
            ).first()
            return account.balance if account else Decimal('0')

    async def update_rounding_settings(
        self,
        user_id: int,
        rounding_step: RoundingStep = None,
        enabled: bool = None
    ):
        """Обновление настроек округления"""
        with self.db.get_session() as session:
            settings = session.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = UserSettings(user_id=user_id)
                session.add(settings)
            
            if rounding_step is not None:
                settings.rounding_step = rounding_step
            if enabled is not None:
                settings.savings_enabled = enabled