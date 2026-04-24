from dataclasses import replace
from datetime import UTC, datetime

from app.application.dto.triage_result import TriageResult
from app.application.ports.classifier_port import ClassifierPort
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.ticket import Ticket
from app.domain.enums.ticket_status import TicketStatus
from app.domain.rules.priority_rules import apply_priority_rules


class TriageTicketUseCase:
    def __init__(
        self,
        classifier: ClassifierPort,
        repository: TicketRepositoryPort,
    ) -> None:
        self.classifier = classifier
        self.repository = repository

    def execute(self, ticket: Ticket) -> TriageResult:
        self.repository.create_ticket(ticket)

        analysis = self.classifier.analyze(ticket)

        analysis = replace(
            analysis,
            suggested_department=analysis.suggested_department or ticket.department,
            model_version=analysis.model_version or "tfidf-mnb-v1",
            analyzed_at=analysis.analyzed_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        )

        ticket.category = ticket.category or analysis.predicted_category.value
        ticket.priority = ticket.priority or analysis.predicted_priority.value
        ticket.team = ticket.team or analysis.suggested_team

        if not ticket.department_locked:
            ticket.department = analysis.suggested_department
        self.repository.attach_analysis(ticket.id, analysis)
        self.repository.update_department(ticket.id, ticket.department)
        self.repository.update_status(ticket.id, TicketStatus.TRIAGED, actor="ai-system")

        final_priority = apply_priority_rules(ticket, analysis.predicted_priority)

        return TriageResult(
            ticket_id=ticket.id,
            analysis=analysis,
            final_priority=final_priority,
            final_category=analysis.predicted_category,
            final_team=analysis.suggested_team,
            ai_recommendation_used=(final_priority == analysis.predicted_priority),
        )
