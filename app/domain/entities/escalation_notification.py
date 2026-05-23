"""An escalation worth telling someone about, out of band.

Emitted by the escalate use case once a ticket has been raised to a higher
priority and reassigned. It carries exactly what a reader in a chat channel
needs to act — and nothing transport-specific. Rendering into Discord,
Slack, or email markup is the job of the NotificationPort adapter, not this
entity, so the same notification can fan out to any channel unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EscalationNotification:
    ticket_id: str
    title: str
    priority: str  # the ticket's priority after escalation, e.g. "critical"
    reason: str
    escalated_by: str | None = None
    team: str | None = None  # target team the ticket was routed to, if any
    assignee: str | None = None
    escalated_at: datetime | None = None
