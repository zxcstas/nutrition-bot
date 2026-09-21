import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from database import init_db
from handlers import basic_router, commands_router, food_input_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main bot entry point"""
    logger.info("Starting Nutrition Bot...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize bot and dispatcher
    bot = Bot(token=settings.telegram_bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_router(basic_router)
    dp.include_router(commands_router)
    dp.include_router(food_input_router)

    logger.info("Routers registered")

    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
