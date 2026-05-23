from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.domain.entities.escalation_notification import EscalationNotification


def test_escalation_notification_keeps_optional_fields_defaulted():
    notification = EscalationNotification(
        ticket_id="DEMO-042",
        title="AML-Verdacht auf Konto",
        priority="critical",
        reason="Regulatorisches Risiko, sofortige Eskalation.",
    )

    assert notification.escalated_by is None
    assert notification.team is None
    assert notification.assignee is None
    assert notification.escalated_at is None


def test_escalation_notification_is_immutable():
    notification = EscalationNotification(
        ticket_id="DEMO-042",
        title="AML-Verdacht auf Konto",
        priority="critical",
        reason="Regulatorisches Risiko.",
        escalated_by="claudio",
        team="compliance-team",
        assignee="maria",
        escalated_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        notification.priority = "high"  # type: ignore[misc]
