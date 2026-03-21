from app.application.dto.triage_result import TriageResult
from app.application.ports.classifier_port import ClassifierPort
from app.domain.entities.ticket import Ticket


class TriageTicketUseCase:
    def __init__(self, classifier: ClassifierPort) -> None:
        self.classifier = classifier

    def execute(self, ticket: Ticket) -> TriageResult:
        return self.classifier.analyze(ticket)
