from datetime import datetime

from sqlalchemy.orm import Session

from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.assignment import Assignment
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_event import TicketEvent
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.domain.enums.ticket_status import TicketStatus
from app.infrastructure.persistence.models import TicketEventModel, TicketRecordModel


class SQLiteTicketRepository(TicketRepositoryPort):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_ticket(self, ticket: Ticket) -> TicketRecord:
        db_record = TicketRecordModel(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            reporter=ticket.reporter,
            source=ticket.source,
            department=ticket.department,
            status=ticket.status.value,
        )
        self.session.add(db_record)
        self.session.commit()
        self.session.refresh(db_record)

        self.add_event(
            ticket_id=ticket.id,
            event_type="ticket_created",
            actor=ticket.reporter,
            summary="Ticket erstellt",
            details=f"Quelle: {ticket.source}",
        )

        return self.get_ticket(ticket.id)

    def attach_analysis(self, ticket_id: str, analysis: TriageAnalysis) -> TicketRecord:
        db_record = self._get_db_record(ticket_id)
        db_record.predicted_category = analysis.predicted_category.value
        db_record.category_confidence = analysis.category_confidence
        db_record.predicted_priority = analysis.predicted_priority.value
        db_record.priority_confidence = analysis.priority_confidence
        db_record.summary = analysis.summary
        db_record.suggested_team = analysis.suggested_team
        db_record.suggested_department = analysis.suggested_department
        db_record.next_step = analysis.next_step
        db_record.rationale = analysis.rationale
        db_record.model_version = analysis.model_version
        db_record.analyzed_at = self._normalize_datetime(analysis.analyzed_at)
        self.session.commit()
        self.session.refresh(db_record)

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

        return self.get_ticket(ticket_id)

    def update_department(self, ticket_id: str, department: str) -> TicketRecord:
        db_record = self._get_db_record(ticket_id)
        db_record.department = department
        self.session.commit()
        self.session.refresh(db_record)
        return self.get_ticket(ticket_id)

    def attach_decision(self, ticket_id: str, decision: TriageDecision) -> TicketRecord:
        db_record = self._get_db_record(ticket_id)
        db_record.final_category = decision.final_category.value
        db_record.final_priority = decision.final_priority.value
        db_record.final_team = decision.final_team
        db_record.accepted_ai_suggestion = decision.accepted_ai_suggestion
        db_record.review_comment = decision.review_comment
        db_record.reviewed_by = decision.reviewed_by
        self.session.commit()
        self.session.refresh(db_record)

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
                + (
                    f", Kommentar={decision.review_comment}"
                    if decision.review_comment
                    else ""
                )
            ),
        )

        return self.get_ticket(ticket_id)

    def attach_assignment(self, ticket_id: str, assignment: Assignment) -> TicketRecord:
        db_record = self._get_db_record(ticket_id)
        db_record.assigned_team = assignment.assigned_team
        db_record.assigned_by = assignment.assigned_by
        db_record.assignment_note = assignment.assignment_note
        self.session.commit()
        self.session.refresh(db_record)

        self.add_event(
            ticket_id=ticket_id,
            event_type="assignment_saved",
            actor=assignment.assigned_by,
            summary="Zuweisung gespeichert",
            details=(
                f"Zugewiesenes Team={assignment.assigned_team}"
                + (
                    f", Notiz={assignment.assignment_note}"
                    if assignment.assignment_note
                    else ""
                )
            ),
        )

        return self.get_ticket(ticket_id)

    def update_status(self, ticket_id: str, status: TicketStatus) -> TicketRecord:
        db_record = self._get_db_record(ticket_id)
        previous_status = db_record.status
        db_record.status = status.value
        self.session.commit()
        self.session.refresh(db_record)

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

        return self.get_ticket(ticket_id)

    def add_event(
        self,
        ticket_id: str,
        event_type: str,
        actor: str | None,
        summary: str,
        details: str | None = None,
    ) -> TicketEvent:
        event = TicketEventModel(
            ticket_id=ticket_id,
            event_type=event_type,
            actor=actor,
            summary=summary,
            details=details,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return self._to_event(event)

    def get_ticket(self, ticket_id: str) -> TicketRecord | None:
        db_record = self.session.get(TicketRecordModel, ticket_id)
        if db_record is None:
            return None
        return self._to_domain_record(db_record)

    def list_tickets(self) -> list[TicketRecord]:
        db_records = self.session.query(TicketRecordModel).all()
        return [self._to_domain_record(record) for record in db_records]

    def _get_db_record(self, ticket_id: str) -> TicketRecordModel:
        db_record = self.session.get(TicketRecordModel, ticket_id)
        if db_record is None:
            raise KeyError(f"Ticket with id '{ticket_id}' not found")
        return db_record

    def _normalize_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(normalized).replace(tzinfo=None)
            except ValueError:
                return datetime.utcnow()
        return datetime.utcnow()

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

    def _to_event(self, event: TicketEventModel) -> TicketEvent:
        return TicketEvent(
            id=event.id,
            ticket_id=event.ticket_id,
            event_type=event.event_type,
            actor=event.actor,
            summary=event.summary,
            details=event.details,
            created_at=event.created_at,
        )

    def _to_domain_record(self, db_record: TicketRecordModel) -> TicketRecord:
        ticket = Ticket(
            title=db_record.title,
            description=db_record.description,
            reporter=db_record.reporter,
            source=db_record.source,
            department=db_record.department,
            department_locked=False,
            status=TicketStatus(db_record.status),
            id=db_record.id,
        )

        analysis = None
        if db_record.predicted_category and db_record.predicted_priority:
            analysis = TriageAnalysis(
                predicted_category=TicketCategory(db_record.predicted_category),
                category_confidence=db_record.category_confidence or 0.0,
                predicted_priority=TicketPriority(db_record.predicted_priority),
                priority_confidence=db_record.priority_confidence or 0.0,
                summary=db_record.summary or "",
                suggested_team=db_record.suggested_team or "",
                suggested_department=db_record.suggested_department or db_record.department,
                next_step=db_record.next_step or "",
                rationale=db_record.rationale or "",
                model_version=db_record.model_version or "unknown",
                analyzed_at=db_record.analyzed_at,
            )

        decision = None
        if db_record.final_category and db_record.final_priority and db_record.final_team:
            decision = TriageDecision(
                final_category=TicketCategory(db_record.final_category),
                final_priority=TicketPriority(db_record.final_priority),
                final_team=db_record.final_team,
                accepted_ai_suggestion=bool(db_record.accepted_ai_suggestion),
                review_comment=db_record.review_comment,
                reviewed_by=db_record.reviewed_by,
            )

        assignment = None
        if db_record.assigned_team:
            assignment = Assignment(
                assigned_team=db_record.assigned_team,
                assigned_by=db_record.assigned_by,
                assignment_note=db_record.assignment_note,
            )

        events = [self._to_event(event) for event in db_record.events]

        return TicketRecord(
            ticket=ticket,
            analysis=analysis,
            decision=decision,
            assignment=assignment,
            events=events,
        )
