from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.ticket import Ticket


class CreateTicketUseCase:
    def __init__(self, repository: TicketRepositoryPort) -> None:
        self.repository = repository

    def execute(self, ticket: Ticket) -> TicketRecord:
        return self.repository.create_ticket(ticket)
