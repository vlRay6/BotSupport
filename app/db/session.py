from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from contextlib import asynccontextmanager
from app.config import settings

engine = create_async_engine(settings.db_url, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
