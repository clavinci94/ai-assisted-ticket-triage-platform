from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort


class AddTicketCommentUseCase:
    def __init__(self, repository: TicketRepositoryPort) -> None:
        self.repository = repository

    def execute(
        self,
        ticket_id: str,
        actor: str | None,
        body: str,
        is_internal: bool = False,
    ) -> TicketRecord:
        normalized_body = body.strip()
        if not normalized_body:
            raise ValueError("Comment body must not be empty")

        self.repository.add_event(
            ticket_id=ticket_id,
            event_type="internal_note_added" if is_internal else "comment_added",
            actor=actor,
            summary="Interne Notiz hinzugefügt" if is_internal else "Kommentar hinzugefügt",
            details=normalized_body,
        )
        return self.repository.get_ticket(ticket_id)
