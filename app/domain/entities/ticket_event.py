from dataclasses import dataclass
from datetime import datetime


@dataclass
class TicketEvent:
    id: int | None
    ticket_id: str
    event_type: str
    actor: str | None
    summary: str
    details: str | None = None
    created_at: datetime | None = None
