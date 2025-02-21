from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta

from utils.keyboards import KeyboardFactory
from services.expenses import ExpensesService
from services.sleep_weight import SleepWeightService
from services.goals import GoalService
from services.analytics import AnalyticsService, ActivityType

navigation_router = Router()

@navigation_router.message(Command("start"))
async def cmd_start(message: Message, analytics_service: AnalyticsService):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Добро пожаловать в персонального помощника!\n\n"
        "Я помогу вам:\n"
        "• 💰 Вести учет расходов и доходов\n"
        "• ⚖️ Отслеживать вес и режим сна\n"
        "• 🏋️‍♂️ Записывать тренировки\n"
        "• 🎯 Достигать поставленных целей\n"
        "• 📊 Анализировать ваш прогресс\n\n"
        "Выберите раздел в меню:",
        reply_markup=KeyboardFactory.get_main_menu()
    )
    
    await analytics_service.log_activity(
        user_id=message.from_user.id,
        action=ActivityType.BOT_STARTED
    )

@navigation_router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu"""
    await message.answer(
        "Выберите раздел:",
        reply_markup=KeyboardFactory.get_main_menu()
    )

@navigation_router.callback_query(F.data.startswith("menu:"))
async def process_menu_navigation(
    callback: CallbackQuery,
    expenses_service: ExpensesService,
    sleep_weight_service: SleepWeightService,
    goals_service: GoalService
):
    """Обработчик навигации по меню"""
    section = callback.data.split(":")[1]
    
    if section == "main":
        await callback.message.edit_text(
            "Выберите раздел:",
            reply_markup=KeyboardFactory.get_main_menu()
        )
    
    elif section == "finances":
        await callback.message.edit_text(
            "💰 Финансы\n\n"
            "• Добавляйте доходы и расходы\n"
            "• Отслеживайте баланс\n"
            "• Контролируйте накопления",
            reply_markup=KeyboardFactory.get_finances_menu()
        )
    
    elif section == "health":
        await callback.message.edit_text(
            "⚖️ Вес и сон\n\n"
            "• Записывайте измерения веса\n"
            "• Отслеживайте режим сна\n"
            "• Анализируйте динамику",
            reply_markup=KeyboardFactory.get_health_menu()
        )
    
    elif section == "workout":
        await callback.message.edit_text(
            "🏋️‍♂️ Тренировки\n\n"
            "• Записывайте упражнения\n"
            "• Следите за прогрессом\n"
            "• Устанавливайте рекорды",
            reply_markup=KeyboardFactory.get_workout_menu()
        )
    
    elif section == "goals":
        await callback.message.edit_text(
            "🎯 Цели\n\n"
            "• Ставьте финансовые цели\n"
            "• Отслеживайте прогресс\n"
            "• Достигайте результатов",
            reply_markup=KeyboardFactory.get_goals_menu()
        )
    
    elif section == "stats":
        stats = await get_user_statistics(
            callback.from_user.id,
            expenses_service,
            sleep_weight_service,
            goals_service
        )
        await callback.message.edit_text(
            stats,
            reply_markup=KeyboardFactory.get_main_menu()
        )
    
    elif section == "settings":
        await callback.message.edit_text(
            "⚙️ Настройки\n\n"
            "• Настройка округления\n"
            "• Уведомления\n"
            "• Формат отчетов\n"
            "• Часовой пояс",
            reply_markup=KeyboardFactory.get_settings_menu()
        )

async def get_user_statistics(
    user_id: int,
    expenses_service: ExpensesService,
    sleep_weight_service: SleepWeightService,
    goals_service: GoalService
) -> str:
    """Формирование общей статистики пользователя"""
    # Получаем данные из разных сервисов
    expenses_stats = await expenses_service.get_balance(user_id)
    weight_stats = await sleep_weight_service.get_weight_stats(user_id)
    sleep_stats = await sleep_weight_service.get_sleep_stats(user_id)
    goals = await goals_service.get_user_goals(user_id)
    
    # Формируем текст статистики
    stats = "📊 Ваша статистика:\n\n"
    
    # Финансы
    stats += "💰 Финансы (текущий месяц):\n"
    stats += f"• Доходы: {expenses_stats['income']:,.2f} ₽\n"
    stats += f"• Расходы: {expenses_stats['expenses']:,.2f} ₽\n"
    stats += f"• Баланс: {expenses_stats['balance']:+,.2f} ₽\n\n"
    
    # Вес
    if weight_stats['current_weight']:
        stats += "⚖️ Вес:\n"
        stats += f"• Текущий: {weight_stats['current_weight']} кг\n"
        if weight_stats['week_start_weight']:
            change = weight_stats['current_weight'] - weight_stats['week_start_weight']
            stats += f"• Изменение за неделю: {change:+.1f} кг\n\n"
    
    # Сон
    if sleep_stats['avg_duration']:
        stats += "😴 Сон:\n"
        stats += f"• Средняя продолжительность: {sleep_stats['avg_duration']:.1f} ч\n"
        stats += f"• Записей за неделю: {sleep_stats['records_count']}\n\n"
    
    # Цели
    if goals:
        stats += "🎯 Активные цели:\n"
        for goal in goals:
            progress = (goal.current_value - goal.start_value) / \
                      (goal.target_value - goal.start_value) * 100
            stats += f"• {goal.title}: {abs(progress):.1f}%\n"
    
    return stats