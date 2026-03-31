from datetime import datetime
from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.application.use_cases.assign_ticket import AssignTicketUseCase
from app.application.use_cases.add_ticket_comment import AddTicketCommentUseCase
from app.application.use_cases.escalate_ticket import EscalateTicketUseCase
from app.application.use_cases.get_ticket import GetTicketUseCase
from app.application.use_cases.list_tickets import ListTicketsUseCase
from app.application.use_cases.review_triage_decision import ReviewTriageDecisionUseCase
from app.application.use_cases.save_triage_decision import SaveTriageDecisionUseCase
from app.application.use_cases.triage_ticket import TriageTicketUseCase
from app.application.use_cases.get_dashboard_analytics import GetDashboardAnalyticsUseCase
from app.application.use_cases.update_ticket_status import UpdateTicketStatusUseCase
from app.domain.entities.assignment import Assignment
from app.domain.enums.ticket_status import TicketStatus
from app.infrastructure.ai.ml_classifier import MLClassifier
from app.infrastructure.persistence.sqlite_ticket_repository import SQLiteTicketRepository
from app.interfaces.api.dependencies import get_db_session, get_ticket_repository
from app.interfaces.api.schemas.ticket_schemas import (
    TicketAssignmentRequest,
    TicketAssignmentResponse,
    DashboardAnalyticsResponse,
    TicketCommentRequest,
    TicketCommentResponse,
    TicketCreateRequest,
    TicketEscalationRequest,
    TicketEscalationResponse,
    TicketListFacetsResponse,
    TicketListItemResponse,
    TicketListResponse,
    TicketRecordResponse,
    TicketStatusUpdateRequest,
    TicketStatusUpdateResponse,
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
        assignee=assignment.assignee,
        assigned_by=assignment.assigned_by,
        assignment_note=assignment.assignment_note,
    )


def _to_status_update_response(
    ticket_id: str,
    status: TicketStatus,
    actor: str | None,
    note: str | None,
) -> TicketStatusUpdateResponse:
    return TicketStatusUpdateResponse(
        ticket_id=ticket_id,
        status=status.value,
        actor=actor,
        note=note,
    )


def _to_comment_response(request: TicketCommentRequest) -> TicketCommentResponse:
    return TicketCommentResponse(
        ticket_id=request.ticket_id,
        actor=request.actor,
        body=request.body,
        is_internal=request.is_internal,
    )


def _to_escalation_response(
    ticket_id: str,
    priority: str,
    team: str | None,
    assignee: str | None,
    escalated_by: str | None,
    reason: str,
) -> TicketEscalationResponse:
    return TicketEscalationResponse(
        ticket_id=ticket_id,
        priority=priority,
        team=team,
        assignee=assignee,
        escalated_by=escalated_by,
        reason=reason,
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
        category=_record_category(record),
        priority=_record_priority(record),
        team=_record_team(record),
        assignee=_record_assignee(record),
        due_at=record.ticket.due_at,
        tags=_record_tags(record),
        sla_breached=record.ticket.sla_breached,
        status=record.ticket.status.value,
        analysis=analysis,
        decision=decision,
        assignment=assignment,
        events=[_to_event_response(event) for event in record.events],
    )


def _normalize(value: str | None) -> str:
    return str(value or "").strip().lower()


def _record_category(record) -> str:
    if record.decision:
        return record.decision.final_category.value
    if record.ticket.category:
        return record.ticket.category
    if record.analysis:
        return record.analysis.predicted_category.value
    return "unknown"


def _record_priority(record) -> str:
    if record.decision:
        return record.decision.final_priority.value
    if record.ticket.priority:
        return record.ticket.priority
    if record.analysis:
        return record.analysis.predicted_priority.value
    return "unknown"


def _record_team(record) -> str | None:
    if record.assignment:
        return record.assignment.assigned_team
    if record.decision:
        return record.decision.final_team
    if record.ticket.team:
        return record.ticket.team
    if record.analysis:
        return record.analysis.suggested_team
    return None


def _record_assignee(record) -> str | None:
    if record.ticket.assignee:
        return record.ticket.assignee
    if record.assignment and record.assignment.assignee:
        return record.assignment.assignee
    if record.assignment and record.assignment.assigned_by:
        return record.assignment.assigned_by
    if record.decision and record.decision.reviewed_by:
        return record.decision.reviewed_by
    return None


def _record_created_at(record):
    if record.events:
        timestamps = [event.created_at for event in record.events if event.created_at]
        if timestamps:
            return min(timestamps)
    if record.analysis and record.analysis.analyzed_at:
        return record.analysis.analyzed_at
    return None


def _record_updated_at(record):
    if record.events:
        timestamps = [event.created_at for event in record.events if event.created_at]
        if timestamps:
            return max(timestamps)
    if record.analysis and record.analysis.analyzed_at:
        return record.analysis.analyzed_at
    return None


def _record_tags(record) -> list[str]:
    tags: list[str] = [tag for tag in record.ticket.tags if str(tag).strip()]

    deduplicated_tags = []
    seen = set()

    for tag in tags:
        normalized = _normalize(tag)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduplicated_tags.append(tag)

    return deduplicated_tags[:4]


def _to_ticket_list_item_response(record) -> TicketListItemResponse:
    return TicketListItemResponse(
        ticket_id=record.ticket.id,
        title=record.ticket.title,
        description=record.ticket.description,
        reporter=record.ticket.reporter,
        source=record.ticket.source,
        department=record.ticket.department,
        status=record.ticket.status.value,
        category=_record_category(record),
        priority=_record_priority(record),
        team=_record_team(record),
        assignee=_record_assignee(record),
        created_at=_record_created_at(record),
        updated_at=_record_updated_at(record),
        due_at=record.ticket.due_at,
        tags=_record_tags(record),
        sla_breached=record.ticket.sla_breached,
    )


def _build_ticket_list_facets(items: list[TicketListItemResponse]) -> TicketListFacetsResponse:
    def unique(values: list[str]) -> list[str]:
        normalized_values = {
            value for value in values if value
        }
        return sorted(normalized_values, key=lambda value: value.lower())

    return TicketListFacetsResponse(
        statuses=unique([item.status for item in items]),
        priorities=unique([item.priority for item in items]),
        departments=unique([item.department for item in items]),
        sources=unique([item.source for item in items]),
    )


def _matches_ticket_view(
    item: TicketListItemResponse,
    view: str,
    operator: str | None,
) -> bool:
    normalized_view = _normalize(view)
    normalized_operator = _normalize(operator)
    normalized_status = _normalize(item.status)
    normalized_priority = _normalize(item.priority)

    if normalized_view == "mine":
        if not normalized_operator:
            return False
        return normalized_operator in {
            _normalize(item.reporter),
            _normalize(item.assignee),
        }

    if normalized_view == "open":
        return normalized_status in {"new", "triaged", "reviewed", "assigned"}

    if normalized_view == "escalations":
        return normalized_priority in {"high", "critical"} and normalized_status in {"new", "triaged", "reviewed", "assigned"}

    return True


def _matches_ticket_filters(
    item: TicketListItemResponse,
    q: str | None,
    status: str | None,
    priority: str | None,
    department: str | None,
    source: str | None,
) -> bool:
    if q:
        normalized_query = _normalize(q)
        haystack = " ".join(
            [
                item.ticket_id,
                item.title,
                item.description,
                item.reporter or "",
                item.department,
                item.category,
                item.priority,
                item.team or "",
                " ".join(item.tags),
            ]
        ).lower()
        if normalized_query not in haystack:
            return False

    if status and _normalize(item.status) != _normalize(status):
        return False

    if priority and _normalize(item.priority) != _normalize(priority):
        return False

    if department and _normalize(item.department) != _normalize(department):
        return False

    if source and _normalize(item.source) != _normalize(source):
        return False

    return True


def _ticket_sort_value(item: TicketListItemResponse, sort_by: str):
    normalized_sort = _normalize(sort_by)

    if normalized_sort == "priority":
        return {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
        }.get(_normalize(item.priority), 0)

    if normalized_sort == "status":
        return {
            "new": 1,
            "triaged": 2,
            "reviewed": 3,
            "assigned": 4,
            "closed": 5,
        }.get(_normalize(item.status), 0)

    if normalized_sort in {"created_at", "updated_at"}:
        return getattr(item, normalized_sort) or datetime.min

    return _normalize(getattr(item, normalized_sort, item.updated_at or item.title))


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
        assignee=request.assignee,
        assigned_by=request.assigned_by,
        assignment_note=request.assignment_note,
    )

    assign_use_case = AssignTicketUseCase(repository=repository)
    updated_record = assign_use_case.execute(request.ticket_id, assignment)

    return _to_assignment_response(updated_record.ticket.id, updated_record.assignment)


@router.post("/status", response_model=TicketStatusUpdateResponse)
def update_ticket_status(
    request: TicketStatusUpdateRequest,
    repository: TicketRepositoryDep,
) -> TicketStatusUpdateResponse:
    get_use_case = GetTicketUseCase(repository=repository)
    record = get_use_case.execute(request.ticket_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        use_case = UpdateTicketStatusUseCase(repository=repository)
        updated_record = use_case.execute(
            ticket_id=request.ticket_id,
            status=request.status,
            actor=request.actor,
            note=request.note,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    return _to_status_update_response(
        updated_record.ticket.id,
        updated_record.ticket.status,
        request.actor,
        request.note,
    )


@router.post("/comments", response_model=TicketCommentResponse)
def add_ticket_comment(
    request: TicketCommentRequest,
    repository: TicketRepositoryDep,
) -> TicketCommentResponse:
    get_use_case = GetTicketUseCase(repository=repository)
    record = get_use_case.execute(request.ticket_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        use_case = AddTicketCommentUseCase(repository=repository)
        use_case.execute(
            ticket_id=request.ticket_id,
            actor=request.actor,
            body=request.body,
            is_internal=request.is_internal,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Comment body must not be empty")

    return _to_comment_response(request)


@router.post("/escalate", response_model=TicketEscalationResponse)
def escalate_ticket(
    request: TicketEscalationRequest,
    repository: TicketRepositoryDep,
) -> TicketEscalationResponse:
    get_use_case = GetTicketUseCase(repository=repository)
    record = get_use_case.execute(request.ticket_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        use_case = EscalateTicketUseCase(repository=repository)
        updated_record = use_case.execute(
            ticket_id=request.ticket_id,
            escalated_by=request.escalated_by,
            reason=request.reason,
            target_team=request.target_team,
            assignee=request.assignee,
            priority=request.priority,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return _to_escalation_response(
        ticket_id=updated_record.ticket.id,
        priority=updated_record.ticket.priority or request.priority,
        team=updated_record.ticket.team,
        assignee=updated_record.ticket.assignee,
        escalated_by=request.escalated_by,
        reason=request.reason,
    )


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
        team_distribution=result.team_distribution,
        management_metrics=result.management_metrics,
        sla_metrics=result.sla_metrics,
        review_funnel=result.review_funnel,
        ai_acceptance=result.ai_acceptance,
        processing_time_by_priority=result.processing_time_by_priority,
        top_assignees=result.top_assignees,
        ticket_volume_over_time=result.ticket_volume_over_time,
        backlog_development=result.backlog_development,
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


@router.get("/workbench", response_model=TicketListResponse)
def list_tickets_workbench(
    repository: TicketRepositoryDep,
    q: str | None = Query(default=None),
    view: str = Query(default="all"),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    department: str | None = Query(default=None),
    source: str | None = Query(default=None),
    sort_by: str = Query(default="updated_at"),
    sort_dir: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    operator: str | None = Query(default=None),
) -> TicketListResponse:
    use_case = ListTicketsUseCase(repository=repository)
    records = use_case.execute()
    items = [_to_ticket_list_item_response(record) for record in records]
    facets = _build_ticket_list_facets(items)

    filtered_items = [
        item
        for item in items
        if _matches_ticket_view(item, view=view, operator=operator)
        and _matches_ticket_filters(
            item,
            q=q,
            status=status,
            priority=priority,
            department=department,
            source=source,
        )
    ]

    reverse = _normalize(sort_dir) != "asc"
    sorted_items = sorted(
        filtered_items,
        key=lambda item: _ticket_sort_value(item, sort_by),
        reverse=reverse,
    )

    total = len(sorted_items)
    total_pages = max(1, ceil(total / page_size)) if total else 1
    current_page = min(page, total_pages)
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size

    return TicketListResponse(
        items=sorted_items[start_index:end_index],
        total=total,
        page=current_page,
        page_size=page_size,
        total_pages=total_pages,
        view=view,
        facets=facets,
    )


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
