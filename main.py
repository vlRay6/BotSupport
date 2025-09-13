import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import engine
from models.ticket import Base
from handlers import start, tickets, admin
from middlewares import DatabaseMiddleware

logging.basicConfig(level=logging.INFO)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    await create_tables()
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