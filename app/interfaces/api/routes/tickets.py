from fastapi import APIRouter

from app.application.use_cases.triage_ticket import TriageTicketUseCase
from app.infrastructure.ai.baseline_classifier import BaselineClassifier
from app.interfaces.api.schemas.ticket_schemas import (
    TicketCreateRequest,
    TriageResponse,
)
from app.interfaces.mappers.ticket_mapper import to_domain_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/triage", response_model=TriageResponse)
def triage_ticket(request: TicketCreateRequest) -> TriageResponse:
    ticket = to_domain_ticket(request)

    use_case = TriageTicketUseCase(classifier=BaselineClassifier())
    result = use_case.execute(ticket)

    return TriageResponse(
        predicted_category=result.predicted_category.value,
        category_confidence=result.category_confidence,
        predicted_priority=result.predicted_priority.value,
        priority_confidence=result.priority_confidence,
        summary=result.summary,
        suggested_team=result.suggested_team,
        rationale=result.rationale,
    )
