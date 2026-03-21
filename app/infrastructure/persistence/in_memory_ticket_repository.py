from datetime import datetime

from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.assignment import Assignment
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_event import TicketEvent
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_status import TicketStatus


class InMemoryTicketRepository(TicketRepositoryPort):
    def __init__(self) -> None:
        self._records: dict[str, TicketRecord] = {}
        self._event_counter = 1

    def create_ticket(self, ticket: Ticket) -> TicketRecord:
        record = TicketRecord(ticket=ticket)
        self._records[ticket.id] = record
        self.add_event(
            ticket_id=ticket.id,
            event_type="ticket_created",
            actor=ticket.reporter,
            summary="Ticket created",
            details=f"Source: {ticket.source}",
        )
        return record

    def attach_analysis(self, ticket_id: str, analysis: TriageAnalysis) -> TicketRecord:
        record = self._records[ticket_id]
        record.analysis = analysis
        self.add_event(
            ticket_id=ticket_id,
            event_type="triage_completed",
            actor="ai-system",
            summary="AI triage completed",
            details=(
                f"Category={analysis.predicted_category.value}, "
                f"Priority={analysis.predicted_priority.value}, "
                f"Suggested team={analysis.suggested_team}"
            ),
        )
        return record

    def attach_decision(self, ticket_id: str, decision: TriageDecision) -> TicketRecord:
        record = self._records[ticket_id]
        record.decision = decision
        self.add_event(
            ticket_id=ticket_id,
            event_type="review_saved",
            actor=decision.reviewed_by,
            summary="Review decision saved",
            details=(
                f"Final category={decision.final_category.value}, "
                f"Final priority={decision.final_priority.value}, "
                f"Final team={decision.final_team}, "
                f"Accepted AI={decision.accepted_ai_suggestion}"
            ),
        )
        return record

    def attach_assignment(self, ticket_id: str, assignment: Assignment) -> TicketRecord:
        record = self._records[ticket_id]
        record.assignment = assignment
        self.add_event(
            ticket_id=ticket_id,
            event_type="assignment_saved",
            actor=assignment.assigned_by,
            summary="Assignment saved",
            details=f"Assigned team={assignment.assigned_team}",
        )
        return record

    def update_status(self, ticket_id: str, status: TicketStatus) -> TicketRecord:
        record = self._records[ticket_id]
        previous_status = record.ticket.status.value
        record.ticket.status = status
        if previous_status != status.value:
            self.add_event(
                ticket_id=ticket_id,
                event_type="status_changed",
                actor="system",
                summary="Ticket status changed",
                details=f"{previous_status} -> {status.value}",
            )
        return record

    def add_event(
        self,
        ticket_id: str,
        event_type: str,
        actor: str | None,
        summary: str,
        details: str | None = None,
    ) -> TicketEvent:
        event = TicketEvent(
            id=self._event_counter,
            ticket_id=ticket_id,
            event_type=event_type,
            actor=actor,
            summary=summary,
            details=details,
            created_at=datetime.utcnow(),
        )
        self._event_counter += 1
        self._records[ticket_id].events.insert(0, event)
        return event

    def get_ticket(self, ticket_id: str) -> TicketRecord | None:
        return self._records.get(ticket_id)

    def list_tickets(self) -> list[TicketRecord]:
        return list(self._records.values())
