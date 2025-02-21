from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Config(BaseSettings):
   """Конфигурация бота"""
   
   # Токен бота
   BOT_TOKEN: str
   
   # Настройки базы данных
   DATABASE_URL: str
   
   # Настройки Redis
   REDIS_URL: str = "redis://localhost:6379/0"
   
   # Временная зона по умолчанию
   DEFAULT_TIMEZONE: str = "Europe/Moscow"
   
   # Директории проекта
   BASE_DIR: Path = Path(__file__).parent.parent.parent
   
   # Настройки логирования
   LOG_LEVEL: str = "INFO"
   LOG_FILE: Optional[Path] = None
   
   # Настройки отчетов
   WEEKLY_REPORT_TIME: str = "10:00"  # Время отправки еженедельных отчетов
   WEEKLY_REPORT_DAY: str = "SAT"     # День отправки еженедельных отчетов
   
   class Config:
       """Настройки для pydantic"""
       env_file = ".env"
       env_file_encoding = "utf-8"
       
       # Пример преобразования переменных окружения
       @classmethod
       def parse_env_var(cls, field_name: str, raw_val: str) -> any:
           if field_name == "BASE_DIR":
               return Path(raw_val)
           if field_name == "LOG_FILE" and raw_val:
               return Path(raw_val)
           return raw_val

   def get_database_args(self) -> dict:
       """Получение аргументов для подключения к БД"""
       return {
           "database_url": self.DATABASE_URL,
           "echo": False,  # Отключаем вывод SQL-запросов
           "pool_size": 5,
           "max_overflow": 10
       }

   def get_redis_args(self) -> dict:
       """Получение аргументов для подключения к Redis"""
       return {
           "url": self.REDIS_URL,
           "encoding": "utf-8",
           "decode_responses": True
       }