from sqlalchemy.orm import Session

from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.domain.enums.ticket_status import TicketStatus
from app.infrastructure.persistence.models import TicketRecordModel


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
            status=ticket.status.value,
        )
        self.session.add(db_record)
        self.session.commit()
        self.session.refresh(db_record)
        return self._to_domain_record(db_record)

    def attach_analysis(self, ticket_id: str, analysis: TriageAnalysis) -> TicketRecord:
        db_record = self._get_db_record(ticket_id)
        db_record.predicted_category = analysis.predicted_category.value
        db_record.category_confidence = analysis.category_confidence
        db_record.predicted_priority = analysis.predicted_priority.value
        db_record.priority_confidence = analysis.priority_confidence
        db_record.summary = analysis.summary
        db_record.suggested_team = analysis.suggested_team
        db_record.next_step = analysis.next_step
        db_record.rationale = analysis.rationale
        self.session.commit()
        self.session.refresh(db_record)
        return self._to_domain_record(db_record)

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
        return self._to_domain_record(db_record)

    def update_status(self, ticket_id: str, status: TicketStatus) -> TicketRecord:
        db_record = self._get_db_record(ticket_id)
        db_record.status = status.value
        self.session.commit()
        self.session.refresh(db_record)
        return self._to_domain_record(db_record)

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

    def _to_domain_record(self, db_record: TicketRecordModel) -> TicketRecord:
        ticket = Ticket(
            title=db_record.title,
            description=db_record.description,
            reporter=db_record.reporter,
            source=db_record.source,
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
                next_step=db_record.next_step or "",
                rationale=db_record.rationale or "",
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

        return TicketRecord(ticket=ticket, analysis=analysis, decision=decision)
