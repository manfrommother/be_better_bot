import asyncio
from src.bot.config import Config
from src.bot.bot import FinanceTrackerBot

async def main():
   # Загрузка конфигурации
   config = Config()
   
   # Создание и запуск бота
   bot = FinanceTrackerBot(
       token=config.BOT_TOKEN,
       db_url=config.DATABASE_URL,
       redis_url=config.REDIS_URL
   )
   await bot.start()

if __name__ == "__main__":
   asyncio.run(main())