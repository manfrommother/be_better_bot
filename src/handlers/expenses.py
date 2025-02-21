# handlers/expenses.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from decimal import Decimal

from models.expenses import CategoryType
from models.savings import RoundingStep
from services.expenses import ExpensesService
from services.analytics import AnalyticsService, ActivityType


expenses_router = Router()


class TransactionStates(StatesGroup):
    """Состояния для создания транзакции"""
    choosing_type = State()        # Выбор типа (доход/расход)
    choosing_category = State()    # Выбор категории
    entering_amount = State()      # Ввод суммы
    entering_description = State() # Ввод описания (опционально)

class CategoryStates(StatesGroup):
    """Состояния для создания категории"""
    choosing_type = State()    # Выбор типа (доход/расход)
    entering_name = State()    # Ввод названия категории

@expenses_router.message(Command("add"))
async def cmd_add_transaction(message: Message):
    """Обработчик команды добавления транзакции"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Доход", callback_data="trans_type:income"),
            InlineKeyboardButton(text="💸 Расход", callback_data="trans_type:expense")
        ]
    ])
    await message.answer(
        "Выберите тип транзакции:",
        reply_markup=keyboard
    )

@expenses_router.callback_query(F.data.startswith("trans_type:"))
async def transaction_type_selected(callback: CallbackQuery, state: FSMContext, expenses_service: ExpensesService):
    """Обработчик выбора типа транзакции"""
    trans_type = callback.data.split(":")[1]
    await state.update_data(transaction_type=trans_type)
    
    # Получаем категории для выбранного типа транзакции
    categories = await expenses_service.get_user_categories(
        callback.from_user.id,
        CategoryType[trans_type.upper()]
    )
    
    # Формируем клавиатуру с категориями
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat.name, callback_data=f"cat:{cat.id}")]
        for cat in categories
    ] + [[InlineKeyboardButton(text="➕ Новая категория", callback_data="new_category")]])
    
    await callback.message.edit_text(
        "Выберите категорию:",
        reply_markup=keyboard
    )
    await state.set_state(TransactionStates.choosing_category)

@expenses_router.callback_query(TransactionStates.choosing_category)
async def category_selected(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора категории"""
    if callback.data == "new_category":
        # Переходим к созданию новой категории
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Доход", callback_data="cat_type:income"),
                InlineKeyboardButton(text="💸 Расход", callback_data="cat_type:expense")
            ]
        ])
        await callback.message.edit_text(
            "Выберите тип новой категории:",
            reply_markup=keyboard
        )
        await state.set_state(CategoryStates.choosing_type)
    else:
        # Сохраняем выбранную категорию
        category_id = int(callback.data.split(":")[1])
        await state.update_data(category_id=category_id)
        await callback.message.edit_text("Введите сумму:")
        await state.set_state(TransactionStates.entering_amount)

@expenses_router.message(TransactionStates.entering_amount)
async def process_amount(message: Message, state: FSMContext, expenses_service: ExpensesService):
    """Обработчик ввода суммы"""
    try:
        amount = Decimal(message.text.replace(',', '.'))
        
        # Получаем настройки пользователя для показа предварительного расчета
        user_settings = await expenses_service.get_user_settings(message.from_user.id)
        
        if user_settings and user_settings.savings_enabled:
            total, savings = expenses_service.calculate_rounding_amount(
                amount,
                user_settings.rounding_step
            )
            await message.answer(
                f"💰 Сумма: {amount} ₽\n"
                f"🔄 Округление: +{savings} ₽\n"
                f"💳 Итого: {total} ₽\n\n"
                "Введите описание транзакции (или отправьте /skip для пропуска):"
            )
        else:
            await message.answer("Введите описание транзакции (или отправьте /skip для пропуска):")
        
        await state.update_data(amount=amount)
        await state.set_state(TransactionStates.entering_description)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму:")

@expenses_router.message(TransactionStates.entering_description)
async def process_description(
    message: Message,
    state: FSMContext,
    expenses_service: ExpensesService,
    analytics_service: AnalyticsService
):
    """Обработчик ввода описания"""
    if message.text == "/skip":
        description = None
    else:
        description = message.text

    # Получаем сохраненные данные
    data = await state.get_data()
    
    # Создаем транзакцию
    transaction, savings = await expenses_service.create_transaction(
        user_id=message.from_user.id,
        category_id=data['category_id'],
        amount=data['amount'],
        description=description
    )
    
    # Логируем действие в аналитику
    await analytics_service.log_activity(
        user_id=message.from_user.id,
        action=ActivityType.EXPENSE_ADDED if data['transaction_type'] == 'expense' 
              else ActivityType.INCOME_ADDED,
        metadata={
            'amount': str(data['amount']),
            'category_id': data['category_id'],
            'savings': str(savings) if savings else None
        }
    )
    
    # Формируем сообщение об успешном добавлении
    response = f"✅ Транзакция добавлена!\n\n"
    response += f"{'Расход' if data['transaction_type'] == 'expense' else 'Доход'}: {data['amount']} ₽\n"
    if description:
        response += f"📝 Описание: {description}\n"
    if savings:
        response += f"💰 На накопительный счёт: {savings} ₽\n"

    await message.answer(response)
    await state.clear()

@expenses_router.message(Command("categories"))
async def cmd_categories(message: Message, expenses_service: ExpensesService):
    """Обработчик команды просмотра категорий"""
    # Получаем все категории пользователя
    income_categories = await expenses_service.get_user_categories(
        message.from_user.id,
        CategoryType.INCOME
    )
    expense_categories = await expenses_service.get_user_categories(
        message.from_user.id,
        CategoryType.EXPENSE
    )
    
    response = "📋 Ваши категории:\n\n"
    
    if income_categories:
        response += "💰 Доходы:\n"
        for cat in income_categories:
            response += f"• {cat.name}\n"
        response += "\n"
    
    if expense_categories:
        response += "💸 Расходы:\n"
        for cat in expense_categories:
            response += f"• {cat.name}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➕ Добавить категорию", callback_data="add_category")
    ]])
    
    await message.answer(response, reply_markup=keyboard)

@expenses_router.message(Command("balance"))
async def cmd_balance(message: Message, expenses_service: ExpensesService):
    """Обработчик команды просмотра баланса"""
    # Получаем баланс за текущий месяц
    start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    balance = await expenses_service.get_balance(
        message.from_user.id,
        start_date=start_date
    )
    
    # Получаем баланс накопительного счета
    savings = await expenses_service.get_savings_balance(message.from_user.id)
    
    # Формируем ответ
    response = "💰 Ваш баланс за текущий месяц:\n\n"
    response += f"Доходы: {balance['income']:,.2f} ₽\n"
    response += f"Расходы: {balance['expenses']:,.2f} ₽\n"
    response += f"Баланс: {balance['balance']:+,.2f} ₽\n"
    
    if savings > 0:
        response += f"\n🏦 Накопительный счёт: {savings:,.2f} ₽"
    
    await message.answer(response)

@expenses_router.callback_query(F.data == "add_category")
async def start_category_creation(callback: CallbackQuery, state: FSMContext):
    """Обработчик начала создания категории"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Доход", callback_data="cat_type:income"),
            InlineKeyboardButton(text="💸 Расход", callback_data="cat_type:expense")
        ]
    ])
    await callback.message.edit_text(
        "Выберите тип категории:",
        reply_markup=keyboard
    )
    await state.set_state(CategoryStates.choosing_type)

@expenses_router.message(Command("settings"))
async def cmd_settings(message: Message, expenses_service: ExpensesService):
    """Обработчик команды настроек округления"""
    # Получаем текущие настройки пользователя
    settings = await expenses_service.get_user_settings(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="10 ₽", callback_data="round:10"),
            InlineKeyboardButton(text="50 ₽", callback_data="round:50"),
            InlineKeyboardButton(text="100 ₽", callback_data="round:100")
        ],
        [
            InlineKeyboardButton(
                text="✅ Округление включено" if settings.savings_enabled else "❌ Округление выключено", 
                callback_data="round:toggle"
            )
        ]
    ])
    
    current_step = settings.rounding_step.value if settings.savings_enabled else "отключено"
    
    await message.answer(
        f"⚙️ Настройки округления\n\n"
        f"Текущий шаг округления: {current_step} ₽\n\n"
        f"Выберите новый шаг округления или включите/выключите округление:",
        reply_markup=keyboard
    )

@expenses_router.callback_query(F.data.startswith("round:"))
async def process_rounding_setting(callback: CallbackQuery, expenses_service: ExpensesService):
    """Обработчик выбора настроек округления"""
    action = callback.data.split(":")[1]
    
    if action == "toggle":
        # Переключаем состояние округления
        settings = await expenses_service.get_user_settings(callback.from_user.id)
        await expenses_service.update_settings(
            user_id=callback.from_user.id,
            savings_enabled=not settings.savings_enabled
        )
        await cmd_settings(callback.message, expenses_service)
    else:
        # Устанавливаем новый шаг округления
        step = RoundingStep[f"STEP_{action}"]
        await expenses_service.update_settings(
            user_id=callback.from_user.id,
            rounding_step=step,
            savings_enabled=True
        )
        await callback.answer(f"Установлено округление до {action} ₽")
        await cmd_settings(callback.message, expenses_service)

# Добавим пример расчета округления
@expenses_router.message(Command("calc"))
async def cmd_calc_rounding(message: Message, expenses_service: ExpensesService):
    """Калькулятор округления"""
    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            "Используйте команду так:\n"
            "/calc <сумма>\n"
            "Например: /calc 156.70"
        )
        return

    try:
        amount = Decimal(args[1].replace(',', '.'))
        settings = await expenses_service.get_user_settings(message.from_user.id)
        
        if not settings.savings_enabled:
            await message.answer(
                "❌ У вас отключено округление.\n"
                "Включите его в настройках: /settings"
            )
            return

        total, savings = expenses_service.calculate_rounding_amount(
            amount,
            settings.rounding_step
        )
        
        await message.answer(
            f"💰 Сумма: {amount} ₽\n"
            f"🔄 Округление: +{savings} ₽\n"
            f"💳 Итого к списанию: {total} ₽\n"
            f"💰 На накопительный счёт: {savings} ₽"
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму")