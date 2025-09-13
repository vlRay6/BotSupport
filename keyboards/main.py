from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📨 Создать обращение")],
            [KeyboardButton(text="📋 Мои обращения"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def get_ticket_keyboard(ticket_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{ticket_id}")],
            [InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"close_{ticket_id}")],
            [InlineKeyboardButton(text="📋 Просмотреть", callback_data=f"view_ticket_{ticket_id}")]
        ]
    )

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="📋 Все обращения")]
        ],
        resize_keyboard=True
    )