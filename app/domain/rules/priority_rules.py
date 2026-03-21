from app.domain.entities.ticket import Ticket
from app.domain.enums.ticket_priority import TicketPriority


def apply_priority_rules(ticket: Ticket, suggested_priority: TicketPriority) -> TicketPriority:
    text = f"{ticket.title} {ticket.description}".lower()

    if any(word in text for word in ["critical", "security", "data loss", "outage", "production down"]):
        return TicketPriority.CRITICAL

    if any(word in text for word in ["urgent", "payment failed", "login failed"]):
        return TicketPriority.HIGH

    return suggested_priority
