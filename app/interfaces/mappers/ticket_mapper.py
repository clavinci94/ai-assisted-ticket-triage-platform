from app.domain.entities.ticket import Ticket
from app.interfaces.api.schemas.ticket_schemas import TicketCreateRequest


def to_domain_ticket(request: TicketCreateRequest) -> Ticket:
    return Ticket(
        title=request.title,
        description=request.description,
        reporter=request.reporter,
        source=request.source,
        department=request.department,
        department_locked=request.department_locked,
    )
