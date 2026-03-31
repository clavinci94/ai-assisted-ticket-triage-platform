from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_status import TicketStatus


class SaveTriageDecisionUseCase:
    def __init__(self, repository: TicketRepositoryPort) -> None:
        self.repository = repository

    def execute(self, ticket_id: str, decision: TriageDecision) -> TicketRecord:
        self.repository.attach_decision(ticket_id, decision)
        updated_record = self.repository.update_status(
            ticket_id,
            TicketStatus.REVIEWED,
            actor=decision.reviewed_by,
        )
        return updated_record
