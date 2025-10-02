from enum import StrEnum


class TicketStatus(StrEnum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
