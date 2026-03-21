from dataclasses import dataclass

from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority


@dataclass
class TriageDecision:
    final_category: TicketCategory
    final_priority: TicketPriority
    final_team: str
    accepted_ai_suggestion: bool
    review_comment: str | None = None
    reviewed_by: str | None = None
