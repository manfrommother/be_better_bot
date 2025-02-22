from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from src.models.workout import Exercise
from src.models.analytics import ActivityType

workout_router = Router()

class ExerciseStates(StatesGroup):
    """Состояния для записи упражнения"""
    entering_name = State()      # Ввод названия упражнения
    entering_weight = State()    # Ввод веса
    entering_reps = State()      # Ввод количества повторений
    entering_sets = State()      # Ввод количества подходов

@workout_router.message(Command("workout"))
async def cmd_workout(message: Message):
    """Обработчик команды записи тренировки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Записать упражнение", callback_data="workout:add"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="workout:stats")
        ],
        [
            InlineKeyboardButton(text="📋 История тренировок", callback_data="workout:history")
        ]
    ])
    await message.answer(
        "🏋️‍♂️ Тренировки\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@workout_router.callback_query(F.data == "workout:add")
async def start_exercise_record(callback: CallbackQuery, state: FSMContext):
    """Начало записи упражнения"""
    await callback.message.edit_text(
        "Введите название упражнения:\n"
        "Например: Жим лежа, Присед, Становая тяга"
    )
    await state.set_state(ExerciseStates.entering_name)

@workout_router.message(ExerciseStates.entering_name)
async def process_exercise_name(message: Message, state: FSMContext):
    """Обработчик ввода названия упражнения"""
    await state.update_data(exercise_name=message.text)
    await message.answer(
        "Введите вес в килограммах:\n"
        "Например: 60.5"
    )
    await state.set_state(ExerciseStates.entering_weight)

@workout_router.message(ExerciseStates.entering_weight)
async def process_weight(message: Message, state: FSMContext):
    """Обработчик ввода веса"""
    try:
        weight = float(message.text.replace(',', '.'))
        await state.update_data(weight=weight)
        await message.answer(
            "Введите количество повторений в подходе:"
        )
        await state.set_state(ExerciseStates.entering_reps)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный вес:")

@workout_router.message(ExerciseStates.entering_reps)
async def process_reps(message: Message, state: FSMContext):
    """Обработчик ввода количества повторений"""
    try:
        reps = int(message.text)
        await state.update_data(reps=reps)
        await message.answer(
            "Введите количество подходов:"
        )
        await state.set_state(ExerciseStates.entering_sets)
    except ValueError:
        await message.answer("Пожалуйста, введите целое число:")

@workout_router.message(ExerciseStates.entering_sets)
async def process_sets(
    message: Message, 
    state: FSMContext, 
    exercise_service,
    analytics_service
):
    """Обработчик ввода количества подходов"""
    try:
        sets = int(message.text)
        data = await state.get_data()
        
        # Создаем запись об упражнении
        exercise = await exercise_service.add_exercise(
            user_id=message.from_user.id,
            name=data['exercise_name'],
            weight=data['weight'],
            reps=data['reps'],
            sets=sets,
            workout_date=datetime.utcnow()
        )
        
        # Логируем в аналитику
        await analytics_service.log_activity(
            user_id=message.from_user.id,
            action=ActivityType.WORKOUT_RECORDED,
            metadata={
                'exercise': data['exercise_name'],
                'weight': data['weight'],
                'reps': data['reps'],
                'sets': sets
            }
        )
        
        # Получаем статистику по этому упражнению
        stats = await exercise_service.get_exercise_stats(
            user_id=message.from_user.id,
            exercise_name=data['exercise_name']
        )
        
        response = (
            f"✅ Упражнение записано!\n\n"
            f"🏋️‍♂️ {data['exercise_name']}\n"
            f"⚖️ Вес: {data['weight']} кг\n"
            f"🔄 Повторений: {data['reps']}\n"
            f"📊 Подходов: {sets}\n\n"
        )
        
        if stats['prev_weight']:
            weight_diff = data['weight'] - stats['prev_weight']
            response += f"Изменение веса: {weight_diff:+.1f} кг\n"
        
        if stats['max_weight']:
            response += f"Ваш рекорд: {stats['max_weight']} кг\n"
        
        await message.answer(response)
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, введите целое число:")

@workout_router.callback_query(F.data == "workout:stats")
async def show_workout_stats(callback: CallbackQuery, exercise_service):
    """Показ статистики тренировок"""
    stats = await exercise_service.get_user_stats(callback.from_user.id)
    
    response = "📊 Статистика тренировок\n\n"
    
    if stats['recent_exercises']:
        response += "🏋️‍♂️ Последние упражнения:\n"
        for exercise in stats['recent_exercises']:
            response += (
                f"• {exercise.name}: "
                f"{exercise.weight} кг × "
                f"{exercise.reps} × "
                f"{exercise.sets}\n"
            )
    
    if stats['max_weights']:
        response += "\n💪 Рекорды:\n"
        for exercise_name, weight in stats['max_weights'].items():
            response += f"• {exercise_name}: {weight} кг\n"
    
    await callback.message.edit_text(
        response,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Назад", callback_data="workout:back")
        ]])
    )

@workout_router.callback_query(F.data == "workout:history")
async def show_workout_history(callback: CallbackQuery, exercise_service):
    """Показ истории тренировок"""
    exercises = await exercise_service.get_user_history(
        user_id=callback.from_user.id,
        limit=10
    )
    
    response = "📋 История тренировок\n\n"
    
    current_date = None
    for exercise in exercises:
        exercise_date = exercise.workout_date.strftime("%d.%m.%Y")
        
        if exercise_date != current_date:
            response += f"\n📅 {exercise_date}\n"
            current_date = exercise_date
        
        response += (
            f"• {exercise.name}: "
            f"{exercise.weight} кг × "
            f"{exercise.reps} × "
            f"{exercise.sets}\n"
        )
    
    await callback.message.edit_text(
        response,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Назад", callback_data="workout:back")
        ]])
    )

@workout_router.callback_query(F.data == "workout:back")
async def workout_back(callback: CallbackQuery):
    """Возврат в главное меню тренировок"""
    await cmd_workout(callback.message)