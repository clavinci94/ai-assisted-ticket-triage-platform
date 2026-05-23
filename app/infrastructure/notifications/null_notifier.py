import logging

from app.application.ports.notification_port import NotificationPort
from app.domain.entities.escalation_notification import EscalationNotification

logger = logging.getLogger(__name__)


class NullNotifier(NotificationPort):
    """The default when no webhook is configured: deliver nowhere.

    Keeps escalation working with zero setup and keeps dev / CI hermetic —
    no network call is ever made. We log at debug so it's visible *why*
    nothing was pushed when someone goes looking.
    """

    def notify_escalation(self, notification: EscalationNotification) -> None:
        logger.debug(
            "Escalation notification suppressed (no notifier configured)",
            extra={"ticket_id": notification.ticket_id},
        )
