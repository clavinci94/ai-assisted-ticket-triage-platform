from dataclasses import dataclass, field
from uuid import uuid4

from app.domain.enums.ticket_status import TicketStatus


@dataclass
class Ticket:
    title: str
    description: str
    reporter: str | None = None
    source: str = "internal"
    status: TicketStatus = TicketStatus.NEW
    id: str = field(default_factory=lambda: str(uuid4()))
