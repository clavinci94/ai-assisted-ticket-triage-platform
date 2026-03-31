from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort


class EscalateTicketUseCase:
    def __init__(self, repository: TicketRepositoryPort) -> None:
        self.repository = repository

    def execute(
        self,
        ticket_id: str,
        escalated_by: str | None,
        reason: str,
        target_team: str | None = None,
        assignee: str | None = None,
        priority: str = "critical",
    ) -> TicketRecord:
        normalized_reason = reason.strip()
        if not normalized_reason:
            raise ValueError("Escalation reason must not be empty")

        updated_record = self.repository.update_ticket_fields(
            ticket_id,
            priority=priority.strip().lower() or "critical",
            team=target_team.strip() if target_team else None,
            assignee=assignee.strip() if assignee else None,
            sla_breached=True,
        )

        self.repository.add_event(
            ticket_id=ticket_id,
            event_type="ticket_escalated",
            actor=escalated_by,
            summary="Ticket eskaliert",
            details=", ".join(
                filter(
                    None,
                    [
                        f"Neue Priorität={updated_record.ticket.priority or priority}",
                        f"Zielteam={target_team.strip()}" if target_team else None,
                        f"Bearbeitung={assignee.strip()}" if assignee else None,
                        f"Grund={normalized_reason}",
                    ],
                )
            ),
        )

        return self.repository.get_ticket(ticket_id)
