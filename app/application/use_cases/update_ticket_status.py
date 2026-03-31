from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.enums.ticket_status import TicketStatus


class UpdateTicketStatusUseCase:
    def __init__(self, repository: TicketRepositoryPort) -> None:
        self.repository = repository

    def execute(
        self,
        ticket_id: str,
        status: str,
        actor: str | None = None,
        note: str | None = None,
    ) -> TicketRecord:
        normalized_status = TicketStatus(str(status).strip().lower())
        return self.repository.update_status(
            ticket_id,
            normalized_status,
            actor=actor,
            note=note,
        )
