from app.domain.entities.ticket import Ticket
from app.interfaces.api.schemas.ticket_schemas import TicketCreateRequest


def to_domain_ticket(request: TicketCreateRequest) -> Ticket:
    return Ticket(
        title=request.title,
        description=request.description,
        reporter=request.reporter,
        source=request.source,
        department=request.department,
        category=request.category,
        priority=request.priority,
        team=request.team,
        assignee=request.assignee,
        due_at=request.due_at,
        tags=request.tags,
        sla_breached=request.sla_breached,
        department_locked=request.department_locked,
    )
