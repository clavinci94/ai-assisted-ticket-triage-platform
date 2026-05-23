import logging
from datetime import UTC, datetime

from app.application.dto.ticket_record import TicketRecord
from app.application.ports.notification_port import NotificationPort
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.escalation_notification import EscalationNotification

logger = logging.getLogger(__name__)


class EscalateTicketUseCase:
    def __init__(
        self,
        repository: TicketRepositoryPort,
        notifier: NotificationPort | None = None,
    ) -> None:
        self.repository = repository
        self.notifier = notifier

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

        record = self.repository.get_ticket(ticket_id)
        self._notify(record, normalized_reason, escalated_by)
        return record

    def _notify(
        self,
        record: TicketRecord,
        reason: str,
        escalated_by: str | None,
    ) -> None:
        """Push the escalation to the configured channel, best-effort.

        A failing notifier is logged and swallowed: a missed chat message
        must never undo an escalation that already persisted (ADR 0005).
        """
        if self.notifier is None:
            return

        ticket = record.ticket
        notification = EscalationNotification(
            ticket_id=ticket.id,
            title=ticket.title,
            priority=ticket.priority or "critical",
            reason=reason,
            escalated_by=escalated_by,
            team=ticket.team,
            assignee=ticket.assignee,
            escalated_at=datetime.now(UTC),
        )

        try:
            self.notifier.notify_escalation(notification)
        except Exception:
            logger.exception(
                "Escalation notification failed",
                extra={"ticket_id": ticket.id},
            )
