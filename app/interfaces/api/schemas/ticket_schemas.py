from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.constants.departments import DEFAULT_DEPARTMENT


class TicketCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5, max_length=5000)
    reporter: str | None = Field(default=None, max_length=100)
    source: str = Field(default="internal", min_length=2, max_length=50)
    department: str = Field(default=DEFAULT_DEPARTMENT, min_length=2, max_length=100)
    department_locked: bool = False


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
    assigned_by: str | None = Field(default=None, max_length=100)
    assignment_note: str | None = Field(default=None, max_length=1000)


class TicketAssignmentResponse(BaseModel):
    ticket_id: str
    assigned_team: str
    assigned_by: str | None
    assignment_note: str | None


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
    status: str
    analysis: TriageAnalysisResponse | None = None
    decision: TriageDecisionResponse | None = None
    assignment: TicketAssignmentResponse | None = None
    events: list[TicketEventResponse] = Field(default_factory=list)


class AnalyticsDistributionItem(BaseModel):
    name: str
    value: int


class DashboardMetricStats(BaseModel):
    total: int
    triaged: int
    reviewed: int
    assigned: int


class ManagementMetricsResponse(BaseModel):
    reviewed_count: int
    accepted_ai_count: int
    acceptance_rate: int
    assignment_rate: int
    review_coverage: int


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
    management_metrics: ManagementMetricsResponse
    review_funnel: list[AnalyticsDistributionItem]
    ai_acceptance: list[AnalyticsDistributionItem]
    needs_attention: list[DashboardTicketSummary]
    recent_activity: list[DashboardTicketSummary]
