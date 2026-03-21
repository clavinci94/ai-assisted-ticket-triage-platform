from enum import Enum


class TicketStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    REVIEWED = "reviewed"
