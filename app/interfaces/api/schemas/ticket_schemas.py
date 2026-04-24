from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.constants.departments import DEFAULT_DEPARTMENT


class TicketCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5, max_length=5000)
    reporter: str | None = Field(default=None, max_length=100)
    source: str = Field(default="internal", min_length=2, max_length=50)
    department: str = Field(default=DEFAULT_DEPARTMENT, min_length=2, max_length=100)
    category: str | None = Field(default=None, max_length=50)
    priority: str | None = Field(default=None, max_length=50)
    team: str | None = Field(default=None, max_length=100)
    assignee: str | None = Field(default=None, max_length=100)
    due_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    sla_breached: bool = False
    department_locked: bool = False


class SimilarCaseResponse(BaseModel):
    ticket_id: str
    title: str
    final_department: str
    final_category: str
    final_team: str | None = None
    similarity_score: float


class TriageAnalysisResponse(BaseModel):
    predicted_category: str
    category_confidence: float
    predicted_priority: str
    priority_confidence: float
    summary: str
    suggested_team: str
    suggested_department: str
    next_step: str
    rationale: str
    model_version: str
    analyzed_at: datetime | None = None
    similar_cases: list[SimilarCaseResponse] = Field(default_factory=list)


class TriageResponse(BaseModel):
    ticket_id: str
    analysis: TriageAnalysisResponse
    final_priority: str
    final_category: str
    final_team: str
    ai_recommendation_used: bool


class TriageDecisionRequest(BaseModel):
    ticket_id: str
    final_category: str = Field(..., min_length=3, max_length=50)
    final_priority: str = Field(..., min_length=3, max_length=50)
    final_team: str = Field(..., min_length=2, max_length=100)
    accepted_ai_suggestion: bool
    review_comment: str | None = Field(default=None, max_length=1000)
    reviewed_by: str | None = Field(default=None, max_length=100)


class TriageDecisionResponse(BaseModel):
    ticket_id: str
    final_category: str
    final_priority: str
    final_team: str
    accepted_ai_suggestion: bool
    review_comment: str | None
    reviewed_by: str | None


class TicketAssignmentRequest(BaseModel):
    ticket_id: str
    assigned_team: str = Field(..., min_length=2, max_length=100)
    assignee: str | None = Field(default=None, max_length=100)
    assigned_by: str | None = Field(default=None, max_length=100)
    assignment_note: str | None = Field(default=None, max_length=1000)


class TicketAssignmentResponse(BaseModel):
    ticket_id: str
    assigned_team: str
    assignee: str | None
    assigned_by: str | None
    assignment_note: str | None


class TicketStatusUpdateRequest(BaseModel):
    ticket_id: str
    status: str = Field(..., min_length=2, max_length=50)
    actor: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=1000)


class TicketStatusUpdateResponse(BaseModel):
    ticket_id: str
    status: str
    actor: str | None
    note: str | None


class TicketCommentRequest(BaseModel):
    ticket_id: str
    actor: str | None = Field(default=None, max_length=100)
    body: str = Field(..., min_length=1, max_length=4000)
    is_internal: bool = False


class TicketCommentResponse(BaseModel):
    ticket_id: str
    actor: str | None
    body: str
    is_internal: bool


class TicketEscalationRequest(BaseModel):
    ticket_id: str
    escalated_by: str | None = Field(default=None, max_length=100)
    reason: str = Field(..., min_length=3, max_length=2000)
    target_team: str | None = Field(default=None, max_length=100)
    assignee: str | None = Field(default=None, max_length=100)
    priority: str = Field(default="critical", min_length=3, max_length=50)


class TicketEscalationResponse(BaseModel):
    ticket_id: str
    priority: str
    team: str | None
    assignee: str | None
    escalated_by: str | None
    reason: str


class TicketEventResponse(BaseModel):
    id: int | None
    ticket_id: str
    event_type: str
    actor: str | None = None
    summary: str
    details: str | None = None
    created_at: datetime | None = None


class TicketRecordResponse(BaseModel):
    ticket_id: str
    title: str
    description: str
    reporter: str | None
    source: str
    department: str
    category: str | None = None
    priority: str | None = None
    team: str | None = None
    assignee: str | None = None
    due_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    sla_breached: bool = False
    status: str
    analysis: TriageAnalysisResponse | None = None
    decision: TriageDecisionResponse | None = None
    assignment: TicketAssignmentResponse | None = None
    events: list[TicketEventResponse] = Field(default_factory=list)


class TicketListItemResponse(BaseModel):
    ticket_id: str
    title: str
    description: str
    reporter: str | None = None
    source: str
    department: str
    status: str
    category: str
    priority: str
    team: str | None = None
    assignee: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    due_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    sla_breached: bool = False


class TicketListFacetsResponse(BaseModel):
    statuses: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class TicketListResponse(BaseModel):
    items: list[TicketListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    view: str
    facets: TicketListFacetsResponse


class AnalyticsDistributionItem(BaseModel):
    name: str
    value: int


class DashboardMetricStats(BaseModel):
    total: int
    triaged: int
    reviewed: int
    assigned: int
    closed: int


class ManagementMetricsResponse(BaseModel):
    reviewed_count: int
    accepted_ai_count: int
    acceptance_rate: int
    assignment_rate: int
    review_coverage: int


class ProcessingTimeMetricResponse(BaseModel):
    priority: str
    average_hours: int
    ticket_count: int


class AssigneePerformanceResponse(BaseModel):
    name: str
    active_count: int
    closed_count: int
    total_count: int


class SlaMetricsResponse(BaseModel):
    total_with_sla: int
    in_sla: int
    due_soon: int
    overdue: int
    breached: int


class TimeSeriesPointResponse(BaseModel):
    date: str
    value: int


class BacklogPointResponse(BaseModel):
    date: str
    created: int
    closed: int
    backlog: int


class DashboardTicketSummary(BaseModel):
    id: str
    title: str
    description: str
    reporter: str | None = None
    status: str
    category: str
    priority: str


class DashboardAnalyticsResponse(BaseModel):
    stats: DashboardMetricStats
    status_distribution: list[AnalyticsDistributionItem]
    category_distribution: list[AnalyticsDistributionItem]
    priority_distribution: list[AnalyticsDistributionItem]
    department_distribution: list[AnalyticsDistributionItem]
    team_distribution: list[AnalyticsDistributionItem]
    management_metrics: ManagementMetricsResponse
    sla_metrics: SlaMetricsResponse
    review_funnel: list[AnalyticsDistributionItem]
    ai_acceptance: list[AnalyticsDistributionItem]
    processing_time_by_priority: list[ProcessingTimeMetricResponse]
    top_assignees: list[AssigneePerformanceResponse]
    ticket_volume_over_time: list[TimeSeriesPointResponse]
    backlog_development: list[BacklogPointResponse]
    needs_attention: list[DashboardTicketSummary]
    recent_activity: list[DashboardTicketSummary]
