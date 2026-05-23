from abc import ABC, abstractmethod

from app.domain.entities.escalation_notification import EscalationNotification


class NotificationPort(ABC):
    @abstractmethod
    def notify_escalation(self, notification: EscalationNotification) -> None:
        """Push an escalation to an out-of-band channel (chat, email, ...).

        Implementations render ``notification`` into their channel's format
        and deliver it. They may raise on delivery failure — callers decide
        whether a failed notification should propagate. The escalate use
        case treats it as best-effort and swallows errors, because a missed
        chat message must never block a state change (ADR 0005).
        """
        raise NotImplementedError
