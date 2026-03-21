from app.domain.entities.ticket import Ticket
from app.domain.enums.ticket_priority import TicketPriority
from app.domain.rules.priority_rules import apply_priority_rules


def test_priority_rules_raise_priority_for_critical_ticket():
    ticket = Ticket(
        title="Production outage",
        description="Critical payment outage with data loss risk",
        reporter="alice",
        source="internal",
    )

    result = apply_priority_rules(ticket, TicketPriority.MEDIUM)

    assert result in {TicketPriority.HIGH, TicketPriority.CRITICAL}
