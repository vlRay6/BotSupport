from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from app.keyboards.main import get_main_keyboard, get_admin_keyboard
from app.config import settings

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id in settings.admin_ids:
        keyboard = get_admin_keyboard()
        text = "👋 Добро пожаловать в панель администратора!"
    else:
        keyboard = get_main_keyboard()
        text = "👋 Добро пожаловать в техподдержку! Выберите действие:"

    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == ("❓ Помощь"))
async def cmd_help(message: Message):
    help_text = """
🤖 Бот техподдержки

📨 Создать обращение - создать новый запрос в поддержку
📋 Мои обращения - просмотреть ваши активные обращения
❓ Помощь - показать это сообщение

"""
    await message.answer(help_text)
