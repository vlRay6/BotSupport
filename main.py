import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import config
from app.handlers import start, tickets, admin
from app.middlewares import DatabaseMiddleware

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DatabaseMiddleware())
    dp.include_router(start.router)
    dp.include_router(tickets.router)
    dp.include_router(admin.router)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
