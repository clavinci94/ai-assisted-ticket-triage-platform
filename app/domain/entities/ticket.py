from dataclasses import dataclass, field
from datetime import datetime
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
    category: str | None = None
    priority: str | None = None
    team: str | None = None
    assignee: str | None = None
    due_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    sla_breached: bool = False
    department_locked: bool = False
    status: TicketStatus = TicketStatus.NEW
    id: str = field(default_factory=lambda: str(uuid4()))
