from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.db.enums import TicketStatus
from app.db.models import Ticket


def my_tickets_keyboard(tickets: list[Ticket]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{
                        '🔓'
                        if ticket.status == TicketStatus.open
                        else '🔒'
                        if ticket.status == TicketStatus.closed
                        else '🔄'
                    } Обращение #{ticket.id} ({ticket.status})",
                    callback_data=f"view_ticket_{ticket.id}",
                )
                for ticket in tickets
            ]
        ]
    )


def my_ticket_keyboard(ticket: Ticket) -> InlineKeyboardMarkup:
    back_button = InlineKeyboardButton(
        text="⬅️ Назад к списку", callback_data="back_to_tickets"
    )

    add_message_button = InlineKeyboardButton(
        text="💬 Добавить сообщение",
        callback_data=f"add_message_{ticket.id}",
    )

    if ticket.status == TicketStatus.open:
        keyboard = [[add_message_button, back_button]]
    else:
        keyboard = [[back_button]]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
