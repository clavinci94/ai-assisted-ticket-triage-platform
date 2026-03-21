from datetime import datetime
from dataclasses import dataclass, field

from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority


@dataclass
class TriageAnalysis:
    predicted_category: TicketCategory
    category_confidence: float
    predicted_priority: TicketPriority
    priority_confidence: float
    summary: str
    suggested_team: str
    next_step: str
    rationale: str
    model_version: str
    analyzed_at: datetime | None = field(default_factory=datetime.utcnow)
