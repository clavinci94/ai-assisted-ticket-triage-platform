from dataclasses import dataclass

from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority


@dataclass
class TriageResult:
    predicted_category: TicketCategory
    category_confidence: float
    predicted_priority: TicketPriority
    priority_confidence: float
    summary: str
    suggested_team: str
    rationale: str
