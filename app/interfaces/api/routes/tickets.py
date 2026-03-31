from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.use_cases.assign_ticket import AssignTicketUseCase
from app.application.use_cases.get_ticket import GetTicketUseCase
from app.application.use_cases.list_tickets import ListTicketsUseCase
from app.application.use_cases.review_triage_decision import ReviewTriageDecisionUseCase
from app.application.use_cases.save_triage_decision import SaveTriageDecisionUseCase
from app.application.use_cases.triage_ticket import TriageTicketUseCase
from app.application.use_cases.get_dashboard_analytics import GetDashboardAnalyticsUseCase
from app.domain.entities.assignment import Assignment
from app.infrastructure.ai.ml_classifier import MLClassifier
from app.infrastructure.persistence.sqlite_ticket_repository import SQLiteTicketRepository
from app.interfaces.api.dependencies import get_db_session, get_ticket_repository
from app.interfaces.api.schemas.ticket_schemas import (
    TicketAssignmentRequest,
    TicketAssignmentResponse,
    DashboardAnalyticsResponse,
    TicketCreateRequest,
    TicketRecordResponse,
    TriageAnalysisResponse,
    TriageDecisionRequest,
    TriageDecisionResponse,
    TriageResponse,
)
from app.interfaces.mappers.ticket_mapper import to_domain_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _to_analysis_response(analysis) -> TriageAnalysisResponse:
    return TriageAnalysisResponse(
        predicted_category=analysis.predicted_category.value,
        category_confidence=analysis.category_confidence,
        predicted_priority=analysis.predicted_priority.value,
        priority_confidence=analysis.priority_confidence,
        summary=analysis.summary,
        suggested_team=analysis.suggested_team,
        suggested_department=analysis.suggested_department,
        next_step=analysis.next_step,
        rationale=analysis.rationale,
        model_version=analysis.model_version,
        analyzed_at=analysis.analyzed_at,
    )


def _to_decision_response(ticket_id: str, decision) -> TriageDecisionResponse:
    return TriageDecisionResponse(
        ticket_id=ticket_id,
        final_category=decision.final_category.value,
        final_priority=decision.final_priority.value,
        final_team=decision.final_team,
        accepted_ai_suggestion=decision.accepted_ai_suggestion,
        review_comment=decision.review_comment,
        reviewed_by=decision.reviewed_by,
    )


def _to_assignment_response(ticket_id: str, assignment) -> TicketAssignmentResponse:
    return TicketAssignmentResponse(
        ticket_id=ticket_id,
        assigned_team=assignment.assigned_team,
        assigned_by=assignment.assigned_by,
        assignment_note=assignment.assignment_note,
    )


def _to_event_response(event):
    return {
        "id": event.id,
        "ticket_id": event.ticket_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "summary": event.summary,
        "details": event.details,
        "created_at": event.created_at,
    }


def _to_ticket_record_response(record) -> TicketRecordResponse:
    analysis = _to_analysis_response(record.analysis) if record.analysis else None
    decision = _to_decision_response(record.ticket.id, record.decision) if record.decision else None
    assignment = _to_assignment_response(record.ticket.id, record.assignment) if record.assignment else None

    return TicketRecordResponse(
        ticket_id=record.ticket.id,
        title=record.ticket.title,
        description=record.ticket.description,
        reporter=record.ticket.reporter,
        source=record.ticket.source,
        department=record.ticket.department,
        status=record.ticket.status.value,
        analysis=analysis,
        decision=decision,
        assignment=assignment,
        events=[_to_event_response(event) for event in record.events],
    )


DbSession = Annotated[Session, Depends(get_db_session)]


def repository_dependency(
    session: DbSession,
) -> SQLiteTicketRepository:
    return get_ticket_repository(session)


TicketRepositoryDep = Annotated[SQLiteTicketRepository, Depends(repository_dependency)]


@router.post("/triage", response_model=TriageResponse)
def triage_ticket(
    request: TicketCreateRequest,
    repository: TicketRepositoryDep,
) -> TriageResponse:
    ticket = to_domain_ticket(request)

    use_case = TriageTicketUseCase(
        classifier=MLClassifier(),
        repository=repository,
    )
    result = use_case.execute(ticket)

    return TriageResponse(
        ticket_id=result.ticket_id,
        analysis=_to_analysis_response(result.analysis),
        final_priority=result.final_priority.value,
        final_category=result.final_category.value,
        final_team=result.final_team,
        ai_recommendation_used=result.ai_recommendation_used,
    )


@router.post("/triage/llm", response_model=TriageResponse)
def triage_ticket_with_llm(
    request: TicketCreateRequest,
    repository: TicketRepositoryDep,
) -> TriageResponse:
    ticket = to_domain_ticket(request)

    try:
        from app.infrastructure.ai.litellm_classifier import LitellmClassifier

        use_case = TriageTicketUseCase(
            classifier=LitellmClassifier(),
            repository=repository,
        )
        result = use_case.execute(ticket)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    return TriageResponse(
        ticket_id=result.ticket_id,
        analysis=_to_analysis_response(result.analysis),
        final_priority=result.final_priority.value,
        final_category=result.final_category.value,
        final_team=result.final_team,
        ai_recommendation_used=result.ai_recommendation_used,
    )


@router.post("/triage/llm/preview", response_model=TriageAnalysisResponse)
def preview_ticket_with_llm(
    request: TicketCreateRequest,
) -> TriageAnalysisResponse:
    ticket = to_domain_ticket(request)

    try:
        from app.infrastructure.ai.litellm_classifier import LitellmClassifier

        analysis = LitellmClassifier().analyze(ticket)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    return _to_analysis_response(analysis)


@router.post("/decision", response_model=TriageDecisionResponse)
def review_triage_decision(
    request: TriageDecisionRequest,
    repository: TicketRepositoryDep,
) -> TriageDecisionResponse:
    get_use_case = GetTicketUseCase(repository=repository)
    record = get_use_case.execute(request.ticket_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    review_use_case = ReviewTriageDecisionUseCase()
    decision = review_use_case.execute(
        final_category=request.final_category,
        final_priority=request.final_priority,
        final_team=request.final_team,
        accepted_ai_suggestion=request.accepted_ai_suggestion,
        review_comment=request.review_comment,
        reviewed_by=request.reviewed_by,
    )

    save_use_case = SaveTriageDecisionUseCase(repository=repository)
    updated_record = save_use_case.execute(request.ticket_id, decision)

    return _to_decision_response(updated_record.ticket.id, updated_record.decision)


@router.post("/assign", response_model=TicketAssignmentResponse)
def assign_ticket(
    request: TicketAssignmentRequest,
    repository: TicketRepositoryDep,
) -> TicketAssignmentResponse:
    get_use_case = GetTicketUseCase(repository=repository)
    record = get_use_case.execute(request.ticket_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    assignment = Assignment(
        assigned_team=request.assigned_team,
        assigned_by=request.assigned_by,
        assignment_note=request.assignment_note,
    )

    assign_use_case = AssignTicketUseCase(repository=repository)
    updated_record = assign_use_case.execute(request.ticket_id, assignment)

    return _to_assignment_response(updated_record.ticket.id, updated_record.assignment)


@router.get("/analytics", response_model=DashboardAnalyticsResponse)
def get_dashboard_analytics(
    repository: TicketRepositoryDep,
) -> DashboardAnalyticsResponse:
    use_case = GetDashboardAnalyticsUseCase(repository=repository)
    result = use_case.execute()

    return DashboardAnalyticsResponse(
        stats=result.stats,
        status_distribution=result.status_distribution,
        category_distribution=result.category_distribution,
        priority_distribution=result.priority_distribution,
        department_distribution=result.department_distribution,
        management_metrics=result.management_metrics,
        review_funnel=result.review_funnel,
        ai_acceptance=result.ai_acceptance,
        needs_attention=result.needs_attention,
        recent_activity=result.recent_activity,
    )


@router.get("", response_model=list[TicketRecordResponse])
def list_tickets(
    repository: TicketRepositoryDep,
) -> list[TicketRecordResponse]:
    use_case = ListTicketsUseCase(repository=repository)
    records = use_case.execute()
    return [_to_ticket_record_response(record) for record in records]


@router.get("/{ticket_id}", response_model=TicketRecordResponse)
def get_ticket(
    ticket_id: str,
    repository: TicketRepositoryDep,
) -> TicketRecordResponse:
    use_case = GetTicketUseCase(repository=repository)
    record = use_case.execute(ticket_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return _to_ticket_record_response(record)
