from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from app.db.session import get_db


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        async with get_db() as session:
            data["session"] = session
            return await handler(event, data)

