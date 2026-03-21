from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.db import Base


class TicketRecordModel(Base):
    __tablename__ = "tickets"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
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
    model_version = Column(String(100), nullable=True)
    analyzed_at = Column(DateTime, nullable=True)

    final_category = Column(String(50), nullable=True)
    final_priority = Column(String(50), nullable=True)
    final_team = Column(String(100), nullable=True)
    accepted_ai_suggestion = Column(Boolean, nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)

    assigned_team = Column(String(100), nullable=True)
    assigned_by = Column(String(100), nullable=True)
    assignment_note = Column(Text, nullable=True)

    events = relationship(
        "TicketEventModel",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketEventModel.created_at.desc()",
    )


class TicketEventModel(Base):
    __tablename__ = "ticket_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(64), ForeignKey("tickets.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=True)
    summary = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    ticket = relationship("TicketRecordModel", back_populates="events")
