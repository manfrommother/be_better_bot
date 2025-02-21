from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, time, timedelta
import re


sleep_weight_router = Router()


class WeightRecordStates(StatesGroup):
    '''Состояние для записи веса'''
    entering_weight = State()

class SleepRecordStates(StatesGroup):
    entering_sleep_time = State()
    entering_wake_time = State()

@sleep_weight_router.message(Command('weight'))
async def cmd_weight(message: Message, state: FSMContext):
    """Обработчик команды записи веса"""
    await message.answer(
        "Введите ваш текущий вес в килограммах (например, 75.5):"
    )
    await state.set_state(WeightRecordStates.entering_weight)

@sleep_weight_router.message(WeightRecordStates.entering_weight)
async def process_weight(message: Message, state: FSMContext, sleep_weight_service):
    """Обработчик ввода веса"""
    try:
        weight = float(message.text.replace(',', '.'))
        if weight < 30 or weight > 250:
            raise ValueError("Вес должен быть в пределах от 30 до 250 кг")
        
        # Записываем вес
        record = await sleep_weight_service.add_weight_record(
            message.from_user.id,
            weight
        )
        
        # Получаем статистику для ответа
        stats = await sleep_weight_service.get_weight_stats(message.from_user.id)
        
        response = f"✅ Вес {weight} кг записан!\n\n"
        
        if stats['previous_weight']:
            change = weight - stats['previous_weight']
            response += f"📊 Изменение с прошлого раза: {change:+.1f} кг\n"
        
        if stats['week_start_weight']:
            week_change = weight - stats['week_start_weight']
            response += f"📈 Изменение за неделю: {week_change:+.1f} кг\n"
        
        # Если есть цель по весу, показываем прогресс
        goal = await sleep_weight_service.get_active_weight_goal(message.from_user.id)
        if goal:
            total_change = weight - goal.start_value
            needed_change = goal.target_value - goal.start_value
            progress = (total_change / needed_change) * 100 if needed_change != 0 else 0
            
            response += f"\n🎯 Прогресс к цели ({goal.target_value} кг):\n"
            response += f"Текущий прогресс: {abs(progress):.1f}%\n"
            response += f"Осталось: {abs(goal.target_value - weight):.1f} кг"
        
        await message.answer(response)
        await state.clear()
        
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}\nПожалуйста, введите корректное значение веса:")

@sleep_weight_router.message(Command("sleep"))
async def cmd_sleep(message: Message, state: FSMContext):
    """Обработчик команды записи сна"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌙 Иду спать", callback_data="sleep:start"),
            InlineKeyboardButton(text="☀️ Проснулся", callback_data="sleep:end")
        ],
        [
            InlineKeyboardButton(text="📝 Записать вручную", callback_data="sleep:manual")
        ]
    ])
    await message.answer(
        "Выберите действие:",
        reply_markup=keyboard
    )

@sleep_weight_router.callback_query(F.data.startswith("sleep:"))
async def process_sleep_action(callback: CallbackQuery, state: FSMContext, sleep_weight_service):
    """Обработчик действий с записью сна"""
    action = callback.data.split(":")[1]
    
    if action == "start":
        # Записываем время начала сна
        await sleep_weight_service.start_sleep_tracking(callback.from_user.id)
        await callback.message.edit_text(
            "🌙 Доброй ночи! Время засыпания записано.\n"
            "Не забудьте отметить время пробуждения командой /sleep"
        )
    
    elif action == "end":
        # Завершаем отслеживание сна
        sleep_record = await sleep_weight_service.end_sleep_tracking(callback.from_user.id)
        if sleep_record:
            duration = sleep_record.wake_time - sleep_record.sleep_time
            hours = duration.total_seconds() / 3600
            
            stats = await sleep_weight_service.get_sleep_stats(callback.from_user.id)
            
            response = (
                f"☀️ Доброе утро!\n\n"
                f"Продолжительность сна: {hours:.1f} часов\n"
            )
            
            if stats['avg_duration']:
                response += f"Средняя продолжительность сна за неделю: {stats['avg_duration']:.1f} часов\n"
            
            if stats['optimal_duration']:
                if hours < stats['optimal_duration']:
                    response += f"\n⚠️ Сегодня вы спали меньше обычного на {stats['optimal_duration'] - hours:.1f} часов"
                elif hours > stats['optimal_duration'] + 2:
                    response += f"\n😴 Сегодня вы спали больше обычного на {hours - stats['optimal_duration']:.1f} часов"
            
            await callback.message.edit_text(response)
        else:
            await callback.message.edit_text(
                "❌ Не найдена запись о времени засыпания.\n"
                "Используйте 'Записать вручную' для ввода полных данных о сне."
            )
    
    elif action == "manual":
        await callback.message.edit_text(
            "Введите время засыпания в формате ЧЧ:ММ\n"
            "Например: 23:30"
        )
        await state.set_state(SleepRecordStates.entering_sleep_time)

@sleep_weight_router.message(SleepRecordStates.entering_sleep_time)
async def process_sleep_time(message: Message, state: FSMContext):
    """Обработчик ввода времени засыпания"""
    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', message.text):
        await message.answer(
            "Пожалуйста, введите время в формате ЧЧ:ММ (например, 23:30):"
        )
        return
    
    await state.update_data(sleep_time=message.text)
    await message.answer(
        "Введите время пробуждения в формате ЧЧ:ММ\n"
        "Например: 07:30"
    )
    await state.set_state(SleepRecordStates.entering_wake_time)