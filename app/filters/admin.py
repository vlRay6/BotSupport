from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from app.config import settings


class IsAdminMessage(Filter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type != "private":
            return False

        return message.chat.id in settings.admin_ids


class IsAdminCallback(Filter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        if (
            not callback.message
            or not callback.message.chat
            or callback.message.chat.type != "private"
        ):
            return False

        return callback.from_user.id in settings.admin_ids
