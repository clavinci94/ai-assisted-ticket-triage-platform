from dataclasses import dataclass, field
from uuid import uuid4

from app.domain.constants.departments import DEFAULT_DEPARTMENT
from app.domain.enums.ticket_status import TicketStatus


@dataclass
class Ticket:
    title: str
    description: str
    reporter: str | None = None
    source: str = "internal"
    department: str = DEFAULT_DEPARTMENT
    department_locked: bool = False
    status: TicketStatus = TicketStatus.NEW
    id: str = field(default_factory=lambda: str(uuid4()))
