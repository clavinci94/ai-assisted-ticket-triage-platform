from dataclasses import dataclass

from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority


@dataclass
class TriageResult:
    ticket_id: str
    analysis: TriageAnalysis
    final_priority: TicketPriority
    final_category: TicketCategory
    final_team: str
    ai_recommendation_used: bool
