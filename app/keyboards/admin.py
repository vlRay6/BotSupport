from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.db.enums import TicketStatus
from app.db.models import Ticket


def all_tickets_keyboard(tickets: list[Ticket]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔓 Открытые", callback_data="filter_open"),
                InlineKeyboardButton(
                    text="🔄 В работе", callback_data="filter_in_progress"
                ),
                InlineKeyboardButton(text="🔒 Закрытые", callback_data="filter_closed"),
            ],
            [InlineKeyboardButton(text="📋 Все", callback_data="filter_all")],
            [
                InlineKeyboardButton(
                    text=f"{
                        '🔓'
                        if ticket.status == TicketStatus.open
                        else '🔄'
                        if ticket.status == TicketStatus.in_progress
                        else '🔒'
                    } #{ticket.id} - {
                        f'@{ticket.username}'
                        if ticket.username
                        else f'{ticket.first_name or ""} {ticket.last_name or ""}'.strip()
                    }",
                    callback_data=f"admin_view_ticket_{ticket.id}",
                )
                for ticket in tickets
            ],
        ]
    )


def one_ticket_keyboard(ticket: Ticket) -> InlineKeyboardMarkup:
    back_button = [
        InlineKeyboardButton(
            text="⬅️ Назад к списку", callback_data="admin_back_to_list"
        )
    ]

    if ticket.status == TicketStatus.closed:
        return InlineKeyboardMarkup(inline_keyboard=[back_button])

    action_row = [
        InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{ticket.id}"),
        InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"close_{ticket.id}"),
    ]

    status_action = (
        ("🔄 Взять в работу", f"take_{ticket.id}")
        if ticket.status == TicketStatus.open
        else ("🔓 Вернуть в открытые", f"reopen_{ticket.id}")
    )

    status_row = [
        InlineKeyboardButton(text=status_action[0], callback_data=status_action[1])
    ]
    return InlineKeyboardMarkup(inline_keyboard=[action_row, status_row, back_button])
