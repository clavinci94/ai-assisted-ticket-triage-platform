from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=5000)
    reporter: str | None = Field(default=None, max_length=100)
    source: str = Field(default="internal", max_length=50)


class TriageResponse(BaseModel):
    predicted_category: str
    category_confidence: float
    predicted_priority: str
    priority_confidence: float
    summary: str
    suggested_team: str
    rationale: str
