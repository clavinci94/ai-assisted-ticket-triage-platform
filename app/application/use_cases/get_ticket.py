from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort


class GetTicketUseCase:
    def __init__(self, repository: TicketRepositoryPort) -> None:
        self.repository = repository

    def execute(self, ticket_id: str) -> TicketRecord | None:
        return self.repository.get_ticket(ticket_id)
