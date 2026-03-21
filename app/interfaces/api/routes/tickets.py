from fastapi import APIRouter

from app.application.use_cases.review_triage_decision import ReviewTriageDecisionUseCase
from app.application.use_cases.triage_ticket import TriageTicketUseCase
from app.infrastructure.ai.baseline_classifier import BaselineClassifier
from app.interfaces.api.schemas.ticket_schemas import (
    TicketCreateRequest,
    TriageAnalysisResponse,
    TriageDecisionRequest,
    TriageDecisionResponse,
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
        analysis=TriageAnalysisResponse(
            predicted_category=result.analysis.predicted_category.value,
            category_confidence=result.analysis.category_confidence,
            predicted_priority=result.analysis.predicted_priority.value,
            priority_confidence=result.analysis.priority_confidence,
            summary=result.analysis.summary,
            suggested_team=result.analysis.suggested_team,
            next_step=result.analysis.next_step,
            rationale=result.analysis.rationale,
        ),
        final_priority=result.final_priority.value,
        final_category=result.final_category.value,
        final_team=result.final_team,
        ai_recommendation_used=result.ai_recommendation_used,
    )


@router.post("/decision", response_model=TriageDecisionResponse)
def review_triage_decision(request: TriageDecisionRequest) -> TriageDecisionResponse:
    use_case = ReviewTriageDecisionUseCase()
    decision = use_case.execute(
        final_category=request.final_category,
        final_priority=request.final_priority,
        final_team=request.final_team,
        accepted_ai_suggestion=request.accepted_ai_suggestion,
        review_comment=request.review_comment,
        reviewed_by=request.reviewed_by,
    )

    return TriageDecisionResponse(
        final_category=decision.final_category.value,
        final_priority=decision.final_priority.value,
        final_team=decision.final_team,
        accepted_ai_suggestion=decision.accepted_ai_suggestion,
        review_comment=decision.review_comment,
        reviewed_by=decision.reviewed_by,
    )
