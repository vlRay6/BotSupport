from aiogram.fsm.state import State, StatesGroup


class TicketStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()
    waiting_for_reply = State()
