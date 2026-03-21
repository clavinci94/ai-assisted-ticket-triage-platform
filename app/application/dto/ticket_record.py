from dataclasses import dataclass, field

from app.domain.entities.assignment import Assignment
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_event import TicketEvent
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.entities.triage_decision import TriageDecision


@dataclass
class TicketRecord:
    ticket: Ticket
    analysis: TriageAnalysis | None = None
    decision: TriageDecision | None = None
    assignment: Assignment | None = None
    events: list[TicketEvent] = field(default_factory=list)
