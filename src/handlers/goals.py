from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


goals_router = Router()


class GoalCreation(StatesGroup):
    '''Состояние для создания целей'''
    choosing_type = State() # Тип цели
    entering_title = State() # Ввод названия
    entering_target = State() # Ввод целевого значения
    entering_deadline = State() # Ввод дедлайна
    entering_description = State() # Ввод названия(опционально)

@goals_router.message(Command('new_goal'))
async def cmd_new_goal(message: Message, state: FSMContext):
    '''Обрабочтик команды создания новой цели'''
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Накопление", callback_data="goal_type:savings"),
            InlineKeyboardButton(text="⚖️ Вес", callback_data="goal_type:weight")
        ]
    ])
    await message.answer(
        'Выберите тип цели:',
        reply_markup=keyboard
    )
    await state.set_state(GoalCreation.choosing_type)

@goals_router.callback_query(F.data.startswith('goal_type:'))
async def goal_type_selected(callback: CallbackQuery, state: FSMContext):
    '''Обработчик выбора типа цели'''
    goal_type = callback.data.split(':')[1]
    await state.update_data(goal_type=goal_type)

    await callback.message.edit_text('Введите название цели:')
    await state.set_state(GoalCreation.entering_title)

@goals_router.message(GoalCreation.entering_title)
async def goal_title_entered(message: Message, state: FSMContext):
    """Обработчик ввода названия цели"""
    await state.update_data(title=message.text)
    
    goal_data = await state.get_data()
    if goal_data['goal_type'] == 'savings':
        await message.answer("Введите сумму, которую хотите накопить (в рублях):")
    else:
        await message.answer("Введите целевой вес (в кг):")
    
    await state.set_state(GoalCreation.entering_target)

@goals_router.message(GoalCreation.entering_target)
async def goal_target_entered(message: Message, state: FSMContext):
    """Обработчик ввода целевого значения"""
    try:
        target_value = float(message.text)
        await state.update_data(target_value=target_value)
        
        await message.answer(
            "Введите дату достижения цели в формате ДД.ММ.ГГГГ:"
        )
        await state.set_state(GoalCreation.entering_deadline)
    except ValueError:
        await message.answer("Пожалуйста, введите число. Попробуйте ещё раз:")