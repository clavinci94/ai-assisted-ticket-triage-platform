from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.assignment import Assignment
from app.domain.enums.ticket_status import TicketStatus


class AssignTicketUseCase:
    def __init__(self, repository: TicketRepositoryPort) -> None:
        self.repository = repository

    def execute(self, ticket_id: str, assignment: Assignment) -> TicketRecord:
        self.repository.attach_assignment(ticket_id, assignment)
        updated_record = self.repository.update_status(ticket_id, TicketStatus.ASSIGNED)
        return updated_record
