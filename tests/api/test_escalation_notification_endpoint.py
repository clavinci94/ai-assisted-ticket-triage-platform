from fastapi.testclient import TestClient

from app.application.ports.notification_port import NotificationPort
from app.interfaces.api.dependencies import get_notifier
from app.main import app

client = TestClient(app)


class CapturingNotifier(NotificationPort):
    def __init__(self):
        self.sent = []

    def notify_escalation(self, notification):
        self.sent.append(notification)


def _create_ticket(title: str) -> str:
    response = client.post(
        "/tickets/triage",
        json={
            "title": title,
            "description": "Eskalations-Benachrichtigung soll hier ausgelöst werden.",
            "reporter": "claudio",
            "source": "internal",
        },
    )
    assert response.status_code == 200
    return response.json()["ticket_id"]


def test_escalation_endpoint_triggers_notification_with_ticket_state():
    notifier = CapturingNotifier()
    app.dependency_overrides[get_notifier] = lambda: notifier
    try:
        ticket_id = _create_ticket("Notify Escalation Test")

        response = client.post(
            "/tickets/escalate",
            json={
                "ticket_id": ticket_id,
                "escalated_by": "claudio",
                "reason": "Produktionsausfall, sofortige Eskalation.",
                "target_team": "incident-response-team",
                "assignee": "maria",
                "priority": "critical",
            },
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_notifier, None)

    assert len(notifier.sent) == 1
    notification = notifier.sent[0]
    assert notification.ticket_id == ticket_id
    assert notification.priority == "critical"
    assert notification.team == "incident-response-team"
    assert notification.assignee == "maria"
    assert "Produktionsausfall" in notification.reason


def test_escalation_endpoint_works_with_default_null_notifier():
    # No override: get_notifier falls back to NullNotifier (no webhook env set).
    ticket_id = _create_ticket("Default Notifier Escalation Test")

    response = client.post(
        "/tickets/escalate",
        json={
            "ticket_id": ticket_id,
            "escalated_by": "claudio",
            "reason": "SLA gefährdet.",
        },
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "critical"
