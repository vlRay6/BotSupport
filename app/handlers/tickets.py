from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Ticket, Message as TicketMessage
from app.keyboards.main import get_ticket_keyboard, get_main_keyboard
from app.config import settings


router = Router()


class TicketStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()
    waiting_for_reply = State()


@router.message(F.text == "📨 Создать обращение")
async def create_ticket_start(message: Message, state: FSMContext):
    await state.set_state(TicketStates.waiting_for_subject)
    await message.answer(
        "📝 Введите тему вашего обращения:", reply_markup=ReplyKeyboardRemove()
    )


@router.message(TicketStates.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(TicketStates.waiting_for_message)
    await message.answer("💬 Теперь опишите вашу проблему подробно:")


@router.message(TicketStates.waiting_for_message)
async def process_message(message: Message, state: FSMContext, session: AsyncSession):
    print(session)
    data = await state.get_data()
    is_additional = data.get("is_additional", False)
    ticket_id = data.get("ticket_id")

    if is_additional and ticket_id:
        ticket = await session.get(Ticket, ticket_id)
        if ticket and ticket.status == "open":
            msg = TicketMessage(
                ticket_id=ticket.id,
                user_id=message.from_user.id,
                message_id=message.message_id,
                text=message.text,
                is_from_user=True,
            )
            session.add(msg)

            if settings.admin_ids:
                admin_text = f"💬 Новое сообщение в обращении #{ticket.id}\n👤 Пользователь: @{message.from_user.username or 'нет'}"
                for admin_id in settings.admin_ids:
                    try:
                        await message.bot.send_message(
                            admin_id,
                            admin_text,
                            reply_markup=get_ticket_keyboard(ticket.id),
                        )
                    except Exception:
                        pass

            await message.answer("✅ Сообщение добавлено!")
        else:
            await message.answer("❌ Нельзя добавить сообщение.")

        await state.clear()
        return
    subject = data.get("subject")
    ticket = Ticket(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    session.add(ticket)
    await session.flush()
    msg = TicketMessage(
        ticket_id=ticket.id,
        user_id=message.from_user.id,
        message_id=message.message_id,
        text=f"Тема: {subject}\n\n{message.text}",
        is_from_user=True,
    )
    session.add(msg)
    admin_text = f"📨 Новое обращение #{ticket.id}\n👤 Пользователь: @{message.from_user.username or 'нет'}\n📝 Тема: {subject}"

    if settings.admin_ids:
        for admin_id in settings.admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    admin_text,
                    reply_markup=get_ticket_keyboard(ticket.id),
                )
            except Exception as e:
                print(f"Error sending to admin {admin_id}: {e}")

    await state.clear()
    await message.answer(
        "✅ Ваше обращение отправлено! Ожидайте ответа от поддержки.",
        reply_markup=get_main_keyboard(),
    )


@router.callback_query(F.data.startswith("reply_"))
async def reply_to_ticket(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split("_")[1])
    await state.set_state(TicketStates.waiting_for_reply)
    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer("💬 Введите ваш ответ:")
    await callback.answer()


@router.message(TicketStates.waiting_for_reply)
async def process_reply(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    ticket_id = data.get("ticket_id")

    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        await message.answer("❌ Обращение не найдено!")
        await state.clear()
        return

    msg = TicketMessage(
        ticket_id=ticket.id,
        user_id=message.from_user.id,
        message_id=message.message_id,
        text=message.text,
        is_from_user=False,
    )
    session.add(msg)

    try:
        await message.bot.send_message(
            ticket.user_id,
            f"📩 Ответ от поддержки по обращению #{ticket.id}:\n\n{message.text}",
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение пользователю: {e}")

    await state.clear()
    await message.answer("✅ Ответ отправлен!")


@router.callback_query(F.data.startswith("close_"))
async def close_ticket(callback: CallbackQuery, session: AsyncSession):
    ticket_id = int(callback.data.split("_")[1])

    ticket = await session.get(Ticket, ticket_id)
    if ticket:
        ticket.status = "closed"
        await session.commit()

        try:
            await callback.bot.send_message(
                ticket.user_id, f"✅ Ваше обращение #{ticket.id} закрыт поддержкой."
            )
        except Exception:
            pass

        await callback.message.edit_text(f"✅ Обращение #{ticket.id} закрыто.")

    await callback.answer()


@router.message(F.text == "📋 Мои обращения")
async def show_my_tickets(message: Message, session: AsyncSession):
    result = await session.execute(
        select(Ticket)
        .where(Ticket.user_id == message.from_user.id)
        .order_by(Ticket.created_at.desc())
    )
    tickets = result.scalars().all()

    if not tickets:
        await message.answer("📭 У вас нет созданных обращений.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for ticket in tickets:
        status_emoji = (
            "🔓"
            if ticket.status == "open"
            else "🔒"
            if ticket.status == "closed"
            else "🔄"
        )
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{status_emoji} Обращение #{ticket.id} ({ticket.status})",
                    callback_data=f"view_ticket_{ticket.id}",
                )
            ]
        )

    await message.answer(f"📋 Ваши обращения ({len(tickets)}):", reply_markup=keyboard)


@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket_details(callback: CallbackQuery, session: AsyncSession):
    ticket_id = int(callback.data.split("_")[2])

    ticket = await session.get(Ticket, ticket_id)
    if not ticket or ticket.user_id != callback.from_user.id:
        await callback.answer("❌ Обращение не найдено!")
        return

    result = await session.execute(
        select(TicketMessage)
        .where(TicketMessage.ticket_id == ticket_id)
        .order_by(TicketMessage.created_at.asc())
    )
    messages = result.scalars().all()

    status_emoji = (
        "🔓" if ticket.status == "open" else "🔒" if ticket.status == "closed" else "🔄"
    )
    text = f"{status_emoji} Обращение #{ticket.id}\n"
    text += f"📅 Создан: {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"📊 Статус: {ticket.status}\n\n"
    text += "💬 Переписка:\n\n"

    for msg in messages:
        sender = "👤 Вы" if msg.is_from_user else "🛠 Поддержка"
        text += f"{sender} ({msg.created_at.strftime('%H:%M')}):\n{msg.text}\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if ticket.status == "open":
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="💬 Добавить сообщение",
                    callback_data=f"add_message_{ticket.id}",
                )
            ]
        )

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_tickets")]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "back_to_tickets")
async def back_to_tickets_list(callback: CallbackQuery):
    await show_my_tickets(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("add_message_"))
async def add_message_to_ticket(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    ticket_id = int(callback.data.split("_")[2])

    ticket = await session.get(Ticket, ticket_id)
    if not ticket or ticket.user_id != callback.from_user.id or ticket.status != "open":
        await callback.answer("❌ Нельзя добавить сообщение к этому обращению!")
        return

    await state.set_state(TicketStates.waiting_for_message)
    await state.update_data(ticket_id=ticket_id, is_additional=True)
    await callback.message.answer("💬 Введите ваше дополнительное сообщение:")
    await callback.answer()
