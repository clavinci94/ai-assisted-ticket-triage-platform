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
            summary="Ticket erstellt",
            details=f"Quelle: {ticket.source}",
        )
        return record

    def attach_analysis(self, ticket_id: str, analysis: TriageAnalysis) -> TicketRecord:
        record = self._records[ticket_id]
        record.analysis = analysis
        self.add_event(
            ticket_id=ticket_id,
            event_type="triage_completed",
            actor="ai-system",
            summary="KI-Triage abgeschlossen",
            details=(
                f"Kategorie={self._format_category(analysis.predicted_category.value)}, "
                f"Priorität={self._format_priority(analysis.predicted_priority.value)}, "
                f"Empfohlene Abteilung={analysis.suggested_department}, "
                f"Empfohlenes Team={analysis.suggested_team}"
            ),
        )
        return record

    def update_department(self, ticket_id: str, department: str) -> TicketRecord:
        record = self._records[ticket_id]
        record.ticket.department = department
        return record

    def attach_decision(self, ticket_id: str, decision: TriageDecision) -> TicketRecord:
        record = self._records[ticket_id]
        record.decision = decision
        self.add_event(
            ticket_id=ticket_id,
            event_type="review_saved",
            actor=decision.reviewed_by,
            summary="Prüfentscheid gespeichert",
            details=(
                f"Endgültige Kategorie={self._format_category(decision.final_category.value)}, "
                f"Endgültige Priorität={self._format_priority(decision.final_priority.value)}, "
                f"Endgültiges Team={decision.final_team}, "
                f"KI akzeptiert={self._format_boolean(decision.accepted_ai_suggestion)}"
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
            summary="Zuweisung gespeichert",
            details=f"Zugewiesenes Team={assignment.assigned_team}",
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
                summary="Ticketstatus geändert",
                details=(
                    f"{self._format_status(previous_status)} -> "
                    f"{self._format_status(status.value)}"
                ),
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

    def _format_category(self, value: str) -> str:
        return {
            "bug": "Fehler",
            "feature": "Funktion",
            "support": "Support",
            "requirement": "Anforderung",
            "question": "Frage",
            "unknown": "Unklar",
        }.get((value or "").lower(), value)

    def _format_priority(self, value: str) -> str:
        return {
            "low": "Niedrig",
            "medium": "Mittel",
            "high": "Hoch",
            "critical": "Kritisch",
        }.get((value or "").lower(), value)

    def _format_status(self, value: str) -> str:
        return {
            "open": "Offen",
            "triaged": "Triage abgeschlossen",
            "reviewed": "Geprüft",
            "assigned": "Zugewiesen",
            "closed": "Geschlossen",
        }.get((value or "").lower(), value)

    def _format_boolean(self, value: bool) -> str:
        return "Ja" if value else "Nein"
