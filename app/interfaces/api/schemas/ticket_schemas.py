from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=5000)
    reporter: str | None = Field(default=None, max_length=100)
    source: str = Field(default="internal", max_length=50)


class TriageAnalysisResponse(BaseModel):
    predicted_category: str
    category_confidence: float
    predicted_priority: str
    priority_confidence: float
    summary: str
    suggested_team: str
    next_step: str
    rationale: str


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


class TicketRecordResponse(BaseModel):
    ticket_id: str
    title: str
    description: str
    reporter: str | None
    source: str
    status: str
    analysis: TriageAnalysisResponse | None = None
    decision: TriageDecisionResponse | None = None
