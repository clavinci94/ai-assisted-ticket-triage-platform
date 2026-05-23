"""Deliver escalations to a Discord channel via an incoming webhook.

Uses the standard library's ``urllib.request`` rather than ``requests`` /
``httpx`` so the runtime gains no new dependency. The payload follows
Discord's webhook shape (``content`` + an ``embeds`` card); a Slack or
Teams adapter would differ only here, behind the same NotificationPort
(ADR 0005).
"""

from __future__ import annotations

import json
import logging
import urllib.request

from app.application.ports.notification_port import NotificationPort
from app.domain.entities.escalation_notification import EscalationNotification

logger = logging.getLogger(__name__)

# Discord embed colours are decimal-encoded RGB. 0xE74C3C — a red sidebar
# that reads as "critical" at a glance.
_CRITICAL_COLOR = 0xE74C3C


class DiscordWebhookNotifier(NotificationPort):
    def __init__(self, webhook_url: str, timeout_seconds: float = 5.0) -> None:
        if not webhook_url:
            raise ValueError("DiscordWebhookNotifier requires a webhook URL")
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def notify_escalation(self, notification: EscalationNotification) -> None:
        payload = self._build_payload(notification)
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        # URL is operator-configured (ESCALATION_WEBHOOK_URL), not user input.
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310
            status = getattr(response, "status", None)
            logger.info(
                "Escalation notification delivered to Discord",
                extra={"ticket_id": notification.ticket_id, "status": status},
            )

    def _build_payload(self, notification: EscalationNotification) -> dict:
        fields = [
            {"name": "Priorität", "value": notification.priority, "inline": True},
        ]
        if notification.team:
            fields.append({"name": "Zielteam", "value": notification.team, "inline": True})
        if notification.assignee:
            fields.append({"name": "Bearbeitung", "value": notification.assignee, "inline": True})
        if notification.escalated_by:
            fields.append({"name": "Eskaliert von", "value": notification.escalated_by, "inline": True})
        fields.append({"name": "Grund", "value": notification.reason, "inline": False})

        embed = {
            "title": f"🚨 Ticket eskaliert: {notification.title}",
            "color": _CRITICAL_COLOR,
            "fields": fields,
        }
        if notification.escalated_at is not None:
            embed["timestamp"] = notification.escalated_at.isoformat()

        return {
            "content": f"🚨 **Eskalation** — Ticket `{notification.ticket_id}`",
            "embeds": [embed],
        }
