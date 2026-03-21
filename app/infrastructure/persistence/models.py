from sqlalchemy import Boolean, Column, Float, String, Text

from app.infrastructure.persistence.db import Base


class TicketRecordModel(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    reporter = Column(String(100), nullable=True)
    source = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    predicted_category = Column(String(50), nullable=True)
    category_confidence = Column(Float, nullable=True)
    predicted_priority = Column(String(50), nullable=True)
    priority_confidence = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    suggested_team = Column(String(100), nullable=True)
    next_step = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)

    final_category = Column(String(50), nullable=True)
    final_priority = Column(String(50), nullable=True)
    final_team = Column(String(100), nullable=True)
    accepted_ai_suggestion = Column(Boolean, nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
