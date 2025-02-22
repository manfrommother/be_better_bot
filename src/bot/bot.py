from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from typing import Dict, Any, Callable, Awaitable
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.handlers.navigation import navigation_router
from handlers.expenses import expenses_router
from handlers.workout import workout_router
from handlers.sleep_weight import sleep_weight_router
from handlers.goals import goals_router

from services.database import DatabaseService
from services.expenses import ExpensesService
from services.sleep_weight import SleepWeightService
from services.goals import GoalService
from services.analytics import AnalyticsService
from services.workout import ExerciseService

class ServicesMiddleware:
   """Middleware для внедрения сервисов в хендлеры"""
   def __init__(self, services: dict):
       self.services = services

   async def __call__(
       self,
       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
       event: Message,
       data: Dict[str, Any]
   ) -> Any:
       # Добавляем сервисы в data, которая будет передана в хендлеры
       data.update(self.services)
       return await handler(event, data)

class FinanceTrackerBot:
   """Основной класс бота"""
   def __init__(self, token: str, db_url: str, redis_url: str):
       # Инициализация бота и диспетчера
       self.bot = Bot(token=token)
       self.storage = RedisStorage.from_url(redis_url)
       self.dp = Dispatcher(storage=self.storage)
       
       # Инициализация базы данных
       self.db = DatabaseService(db_url)
       self.db.create_tables()
       
       # Инициализация сервисов
       self.services = {
           'db_service': self.db,
           'expenses_service': ExpensesService(self.db),
           'sleep_weight_service': SleepWeightService(self.db),
           'goals_service': GoalService(self.db),
           'analytics_service': AnalyticsService(self.db),
           'workout_service': ExerciseService(self.db)
       }
       
       # Настройка планировщика
       self.scheduler = AsyncIOScheduler()
       
       # Инициализация middleware
       self._setup_middleware()
       
       # Регистрация роутеров
       self._setup_routers()

   def _setup_middleware(self):
       """Настройка middleware"""
       # Middleware для сервисов
       self.dp.message.middleware(ServicesMiddleware(self.services))
       self.dp.callback_query.middleware(ServicesMiddleware(self.services))
       
       # Middleware для автоматического ответа на callback_query
       self.dp.callback_query.middleware(CallbackAnswerMiddleware())

   def _setup_routers(self):
       """Регистрация всех роутеров"""
       # Основные роутеры
       self.dp.include_router(navigation_router)
       self.dp.include_router(expenses_router)
       self.dp.include_router(workout_router)
       self.dp.include_router(sleep_weight_router)
       self.dp.include_router(goals_router)

   async def _setup_scheduler(self):
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
           self.services['goals_service'].check_overdue_goals,
           trigger='cron',
           hour=0,
           minute=0
       )
       
       self.scheduler.start()

   async def start(self):
       """Запуск бота"""
       try:
           # Настройка и запуск планировщика
           await self._setup_scheduler()
           
           # Запуск бота
           await self.dp.start_polling(self.bot)
       finally:
           await self.storage.close()
           await self.bot.session.close()
