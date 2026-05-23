import pytest

from app.application.dto.ticket_record import TicketRecord
from app.application.use_cases.escalate_ticket import EscalateTicketUseCase
from app.domain.entities.escalation_notification import EscalationNotification
from app.domain.entities.ticket import Ticket


class FakeRepository:
    def __init__(self, ticket: Ticket):
        self.ticket = ticket
        self.events = []

    def update_ticket_fields(self, ticket_id, **fields):
        for key, value in fields.items():
            if value is not None:
                setattr(self.ticket, key, value)
        return TicketRecord(ticket=self.ticket)

    def add_event(self, **kwargs):
        self.events.append(kwargs)

    def get_ticket(self, ticket_id):
        return TicketRecord(ticket=self.ticket)


class CapturingNotifier:
    def __init__(self):
        self.sent: list[EscalationNotification] = []

    def notify_escalation(self, notification):
        self.sent.append(notification)


class ExplodingNotifier:
    def __init__(self):
        self.called = False

    def notify_escalation(self, notification):
        self.called = True
        raise RuntimeError("webhook unreachable")


def _ticket() -> Ticket:
    return Ticket(
        title="AML-Verdacht auf Konto",
        description="Verdächtige Transaktionsmuster gemeldet.",
        reporter="alice",
        source="internal",
    )


def test_escalation_notifies_with_post_escalation_state():
    repository = FakeRepository(_ticket())
    notifier = CapturingNotifier()
    use_case = EscalateTicketUseCase(repository=repository, notifier=notifier)

    use_case.execute(
        ticket_id=repository.ticket.id,
        escalated_by="claudio",
        reason="Regulatorisches Risiko, sofortige Eskalation.",
        target_team="compliance-team",
        assignee="maria",
        priority="critical",
    )

    assert len(notifier.sent) == 1
    notification = notifier.sent[0]
    assert notification.ticket_id == repository.ticket.id
    assert notification.title == "AML-Verdacht auf Konto"
    assert notification.priority == "critical"
    assert notification.team == "compliance-team"
    assert notification.assignee == "maria"
    assert notification.escalated_by == "claudio"
    assert "Regulatorisches Risiko" in notification.reason


def test_escalation_succeeds_even_when_notifier_raises():
    repository = FakeRepository(_ticket())
    notifier = ExplodingNotifier()
    use_case = EscalateTicketUseCase(repository=repository, notifier=notifier)

    record = use_case.execute(
        ticket_id=repository.ticket.id,
        escalated_by="claudio",
        reason="SLA akut gefährdet.",
    )

    assert notifier.called is True
    assert record.ticket.priority == "critical"
    assert record.ticket.sla_breached is True
    assert any(event["event_type"] == "ticket_escalated" for event in repository.events)


def test_escalation_without_notifier_is_a_noop():
    repository = FakeRepository(_ticket())
    use_case = EscalateTicketUseCase(repository=repository)

    record = use_case.execute(
        ticket_id=repository.ticket.id,
        escalated_by="claudio",
        reason="Kundenauswirkung hoch.",
    )

    assert record.ticket.priority == "critical"


def test_escalation_rejects_empty_reason():
    repository = FakeRepository(_ticket())
    notifier = CapturingNotifier()
    use_case = EscalateTicketUseCase(repository=repository, notifier=notifier)

    with pytest.raises(ValueError, match="reason must not be empty"):
        use_case.execute(
            ticket_id=repository.ticket.id,
            escalated_by="claudio",
            reason="   ",
        )

    assert notifier.sent == []
