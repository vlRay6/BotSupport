from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.enums import TicketStatus
from app.db.models import Ticket, Message as TicketMessage
from app.config import settings

router = Router()


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message, session: AsyncSession):
    if message.from_user.id not in settings.admin_ids:
        return

    total_tickets = await session.scalar(select(func.count(Ticket.id)))
    open_tickets = await session.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.open)
    )
    closed_tickets = await session.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.closed)
    )
    in_progress_tickets = await session.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.in_progress)
    )

    stats_text = f"""
📊 Статистика обращений:

📨 Всего обращений: {total_tickets}
🔓 Открытых: {open_tickets}
🔄 В работе: {in_progress_tickets}
🔒 Закрытых: {closed_tickets}
"""
    await message.answer(stats_text)


@router.message(F.text == "📋 Все обращения")
async def show_all_tickets(message: Message, session: AsyncSession):
    if message.from_user.id not in settings.admin_ids:
        return

    result = await session.execute(
        select(Ticket).order_by(desc(Ticket.created_at)).limit(50)
    )
    tickets = result.scalars().all()

    if not tickets:
        await message.answer("📭 Нет созданных обращений.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(text="🔓 Открытые", callback_data="filter_open"),
            InlineKeyboardButton(
                text="🔄 В работе", callback_data="filter_in_progress"
            ),
            InlineKeyboardButton(text="🔒 Закрытые", callback_data="filter_closed"),
        ]
    )

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="📋 Все", callback_data="filter_all")]
    )

    for ticket in tickets:
        status_emoji = (
            "🔓"
            if ticket.status == TicketStatus.open
            else "🔄"
            if ticket.status == TicketStatus.in_progress
            else "🔒"
        )
        username = (
            f"@{ticket.username}"
            if ticket.username
            else f"{ticket.first_name or ''} {ticket.last_name or ''}".strip()
        )

        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{status_emoji} #{ticket.id} - {username}",
                    callback_data=f"admin_view_ticket_{ticket.id}",
                )
            ]
        )

    await message.answer(f"📋 Все обращения ({len(tickets)}):", reply_markup=keyboard)


@router.callback_query(F.data.startswith("filter_"))
async def filter_tickets(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен!")
        return

    filter_type = callback.data.split("_")[1]

    if filter_type == "all":
        result = await session.execute(
            select(Ticket).order_by(desc(Ticket.created_at)).limit(50)
        )
    else:
        result = await session.execute(
            select(Ticket)
            .where(Ticket.status == filter_type)
            .order_by(desc(Ticket.created_at))
            .limit(50)
        )

    tickets = result.scalars().all()

    if not tickets:
        await callback.message.edit_text("📭 Нет обращений с выбранным фильтром.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(text="🔓 Открытые", callback_data="filter_open"),
            InlineKeyboardButton(
                text="🔄 В работе", callback_data="filter_in_progress"
            ),
            InlineKeyboardButton(text="🔒 Закрытые", callback_data="filter_closed"),
        ]
    )

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="📋 Все", callback_data="filter_all")]
    )

    for ticket in tickets:
        status_emoji = (
            "🔓"
            if ticket.status == TicketStatus.open
            else "🔄"
            if ticket.status == TicketStatus.in_progress
            else "🔒"
        )
        username = (
            f"@{ticket.username}"
            if ticket.username
            else f"{ticket.first_name or ''} {ticket.last_name or ''}".strip()
        )

        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{status_emoji} #{ticket.id} - {username}",
                    callback_data=f"admin_view_ticket_{ticket.id}",
                )
            ]
        )

    filter_name = "все" if filter_type == "all" else filter_type
    await callback.message.edit_text(
        f"📋 Обращения ({filter_name}): {len(tickets)}", reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_ticket_"))
async def admin_view_ticket_details(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен!")
        return

    ticket_id = int(callback.data.split("_")[3])

    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        await callback.answer("❌ Обращение не найдено!")
        return

    result = await session.execute(
        select(TicketMessage)
        .where(TicketMessage.ticket_id == ticket_id)
        .order_by(TicketMessage.created_at.asc())
    )
    messages = result.scalars().all()

    status_emoji = (
        "🔓"
        if ticket.status == TicketStatus.open
        else "🔄"
        if ticket.status == TicketStatus.in_progress
        else "🔒"
    )
    username = (
        f"@{ticket.username}"
        if ticket.username
        else f"{ticket.first_name or ''} {ticket.last_name or ''}".strip()
    )

    text = f"{status_emoji} Обращение #{ticket.id}\n"
    text += f"👤 Пользователь: {username} (ID: {ticket.user_id})\n"
    text += f"📅 Создан: {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"📊 Статус: {ticket.status}\n\n"
    text += "💬 Переписка:\n\n"

    for msg in messages:
        sender = "👤 Пользователь" if msg.is_from_user else "🛠 Поддержка"
        text += f"{sender} ({msg.created_at.strftime('%H:%M')}):\n{msg.text}\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if ticket.status != "closed":
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="💬 Ответить", callback_data=f"reply_{ticket.id}"
                ),
                InlineKeyboardButton(
                    text="🔒 Закрыть", callback_data=f"close_{ticket.id}"
                ),
            ]
        )

        if ticket.status == TicketStatus.open:
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text="🔄 Взять в работу", callback_data=f"take_{ticket.id}"
                    )
                ]
            )
        else:
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text="🔓 Вернуть в открытые",
                        callback_data=f"reopen_{ticket.id}",
                    )
                ]
            )

    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад к списку", callback_data="admin_back_to_list"
            )
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_back_to_list")
async def admin_back_to_tickets_list(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен!")
        return

    await show_all_tickets(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("take_"))
async def take_ticket(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен!")
        return

    ticket_id = int(callback.data.split("_")[1])

    ticket = await session.get(Ticket, ticket_id)
    if not ticket or ticket.status != "open":
        await callback.answer("❌ Нельзя взять это обращение в работу!")
        return

    ticket.status = TicketStatus.in_progress
    await session.commit()

    try:
        await callback.bot.send_message(
            ticket.user_id,
            f"🔄 Ваше обращение #{ticket.id} взято в работу администратором.",
        )
    except Exception:
        pass

    await callback.answer("✅ Обращение взято в работу!")

    await admin_view_ticket_details(callback)


@router.callback_query(F.data.startswith("reopen_"))
async def reopen_ticket(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("❌ Доступ запрещен!")
        return

    ticket_id = int(callback.data.split("_")[1])

    ticket = await session.get(Ticket, ticket_id)
    if not ticket or ticket.status != "in_progress":
        await callback.answer("❌ Нельзя вернуть это обращение в открытые!")
        return

    ticket.status = TicketStatus.open
    await session.commit()

    await callback.answer("✅ Обращение возвращено в открытые!")
    await admin_view_ticket_details(callback)
