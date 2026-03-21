from app.application.dto.triage_result import TriageResult
from app.application.ports.classifier_port import ClassifierPort
from app.domain.entities.ticket import Ticket
from app.domain.rules.priority_rules import apply_priority_rules


class TriageTicketUseCase:
    def __init__(self, classifier: ClassifierPort) -> None:
        self.classifier = classifier

    def execute(self, ticket: Ticket) -> TriageResult:
        analysis = self.classifier.analyze(ticket)
        final_priority = apply_priority_rules(ticket, analysis.predicted_priority)

        return TriageResult(
            analysis=analysis,
            final_priority=final_priority,
            final_category=analysis.predicted_category,
            final_team=analysis.suggested_team,
            ai_recommendation_used=(final_priority == analysis.predicted_priority),
        )
