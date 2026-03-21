from dataclasses import dataclass

from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.entities.triage_decision import TriageDecision


@dataclass
class TicketRecord:
    ticket: Ticket
    analysis: TriageAnalysis | None = None
    decision: TriageDecision | None = None
