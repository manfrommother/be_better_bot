from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time

from services.database import DatabaseService
from services.analytics import AnalyticsService
from services.goals import GoalService
from handlers.goals import goals_router
from handlers.expenses import expenses_router
import logging


class FinanceTrackerBot:
    '''Основной класс бота'''
    def __init__(self, token: str, db_url: str):
        self.bot = Bot(token=token)
        self.storage = RedisStorage.from_url('redis://localhost:6379/0')
        self.dp = Dispatcher(storage=self.storage)

        # Инициализация сервисов
        self.db = DatabaseService(db_url)
        self.analytics = AnalyticsService(self.db)
        self.goals = GoalService(self.db)

        #Инициализация планировщика
        self.scheduler = AsyncIOScheduler()

        #Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def setup(self):
        """Настройка бота и подключение обработчиков"""
        # Регистрация роутеров
        self.dp.include_router(goals_router)
        self.dp.include_router(expenses_router)
        self.dp.include_router(workout_router)
        self.dp.include_router(sleep_weight_router)
        
        # Настройка планировщика задач
        self._setup_scheduler()
        
        # Создание таблиц в БД, если они не существуют
        self.db.create_tables()
        
        self.logger.info("Бот успешно настроен и готов к работе")

    def _setup_scheduler(self):
        """Настройка планировщика задач"""
        # Еженедельный отчет по субботам в 10:00
        self.scheduler.add_job(
            self._send_weekly_report,
            trigger='cron',
            day_of_week='sat',
            hour=10,
            minute=0
        )
        
        # Ежедневная проверка просроченных целей
        self.scheduler.add_job(
            self.goals.check_overdue_goals,
            trigger='cron',
            hour=0,
            minute=0
        )
        
        self.scheduler.start()

    async def _send_weekly_report(self):
        """Отправка еженедельного отчета"""
        users = await self._get_active_users()
        for user_id in users:
            try:
                report = await self._generate_weekly_report(user_id)
                await self.bot.send_message(user_id, report)
                await self.analytics.collect_user_activity(user_id, "weekly_report_sent")
            except Exception as e:
                self.logger.error(f"Ошибка при отправке отчета пользователю {user_id}: {e}")

    async def _generate_weekly_report(self, user_id: int) -> str:
        """Генерация еженедельного отчета для пользователя"""
        # Получение данных за неделю
        sleep_stats = await self._get_sleep_stats(user_id)
        weight_stats = await self._get_weight_stats(user_id)
        finance_stats = await self._get_finance_stats(user_id)
        goals_progress = await self._get_goals_progress(user_id)
        
        # Формирование отчета
        report = "📊 Ваш еженедельный отчет:\n\n"
        
        # Добавление информации о сне
        report += f"😴 Сон:\n"
        report += f"Среднее время сна: {sleep_stats['average_duration']:.1f} часов\n\n"
        
        # Добавление информации о весе
        if weight_stats['has_records']:
            report += f"⚖️ Вес:\n"
            report += f"Начало недели: {weight_stats['start_weight']} кг\n"
            report += f"Конец недели: {weight_stats['end_weight']} кг\n"
            report += f"Изменение: {weight_stats['change']:+.1f} кг\n\n"
        
        # Добавление финансовой информации
        report += f"💰 Финансы:\n"
        report += f"Доходы: {finance_stats['income']:,.2f} ₽\n"
        report += f"Расходы: {finance_stats['expenses']:,.2f} ₽\n"
        report += f"Баланс: {finance_stats['balance']:+,.2f} ₽\n\n"
        
        # Добавление информации о целях
        if goals_progress:
            report += "🎯 Прогресс по целям:\n"
            for goal in goals_progress:
                progress = (goal.current_value - goal.start_value) / (goal.target_value - goal.start_value) * 100
                report += f"{goal.title}: {progress:.1f}%\n"
        
        return report

    async def run(self):
        """Запуск бота"""
        await self.setup()
        try:
            await self.dp.start_polling(self.bot)
        finally:
            await self.bot.session.close()
