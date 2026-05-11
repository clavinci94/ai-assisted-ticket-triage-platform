"""Backfill prioritisation for tickets that pre-date the KE layer.

For every ticket where ``impact_score IS NULL`` we synthesise the minimal
inputs the prioritizer needs (a ``Ticket`` plus a ``TriageAnalysis``
built from whatever classification fields the row already has), look up
similar reviewed tickets for effort estimation, and persist the result.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.prioritization_port import PrioritizationPort
from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.domain.enums.ticket_status import TicketStatus
from app.infrastructure.persistence.db import SessionLocal
from app.infrastructure.persistence.models import TicketRecordModel
from app.infrastructure.persistence.sqlite_ticket_repository import (
    SQLiteTicketRepository,
)


@dataclass
class BackfillResult:
    candidates: int
    prioritized: int
    skipped: int
    failed: int


class BackfillPrioritizationUseCase:
    def __init__(
        self,
        prioritizer: PrioritizationPort,
        similar_tickets: SimilarTicketsPort,
    ) -> None:
        self.prioritizer = prioritizer
        self.similar_tickets = similar_tickets

    def execute(self) -> BackfillResult:
        candidates = 0
        prioritized = 0
        skipped = 0
        failed = 0

        session = SessionLocal()
        try:
            rows = session.query(TicketRecordModel).filter(TicketRecordModel.impact_score.is_(None)).all()
            candidates = len(rows)
            repo = SQLiteTicketRepository(session)

            for row in rows:
                try:
                    ticket = _to_synthetic_ticket(row)
                    analysis = _to_synthetic_analysis(row)
                    probe = f"{row.title or ''} {row.description or ''}".strip()
                    cases = self.similar_tickets.find_similar(probe, top_k=5) if probe else []
                    prio = self.prioritizer.prioritize(ticket, analysis, similar_cases=cases)
                    repo.attach_prioritization(row.id, prio)
                    prioritized += 1
                except KeyboardInterrupt:
                    raise
                except Exception:
                    session.rollback()
                    failed += 1
                    continue
        finally:
            session.close()

        skipped = candidates - prioritized - failed
        return BackfillResult(
            candidates=candidates,
            prioritized=prioritized,
            skipped=skipped,
            failed=failed,
        )


def _to_synthetic_ticket(row: TicketRecordModel) -> Ticket:
    tags_raw = row.tags or ""
    tags: list[str] = []
    if tags_raw:
        try:
            import json

            parsed = json.loads(tags_raw)
            if isinstance(parsed, list):
                tags = [str(t) for t in parsed]
        except (ValueError, TypeError):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    try:
        status = TicketStatus(row.status or "new")
    except ValueError:
        status = TicketStatus.NEW

    return Ticket(
        id=row.id,
        title=row.title or "",
        description=row.description or "",
        reporter=row.reporter,
        source=row.source or "internal",
        department=row.department or "Bank-IT Support",
        category=row.final_category or row.category,
        priority=row.final_priority or row.priority,
        team=row.final_team or row.team,
        assignee=row.assignee,
        due_at=row.due_at,
        tags=tags,
        sla_breached=bool(row.sla_breached),
        status=status,
        department_locked=True,
    )


def _to_synthetic_analysis(row: TicketRecordModel) -> TriageAnalysis:
    category_value = (
        row.predicted_category or row.final_category or row.category or TicketCategory.UNKNOWN.value
    )
    try:
        category = TicketCategory(category_value)
    except ValueError:
        category = TicketCategory.UNKNOWN

    priority_value = (
        row.predicted_priority or row.final_priority or row.priority or TicketPriority.MEDIUM.value
    )
    try:
        priority = TicketPriority(priority_value)
    except ValueError:
        priority = TicketPriority.MEDIUM

    confidence = float(row.category_confidence or 0.5)

    return TriageAnalysis(
        predicted_category=category,
        category_confidence=confidence,
        predicted_priority=priority,
        priority_confidence=float(row.priority_confidence or confidence),
        summary=row.summary or "",
        suggested_team=row.suggested_team or row.team or "",
        suggested_department=row.suggested_department or row.department or "",
        next_step=row.next_step or "",
        rationale=row.rationale or "",
        model_version=row.model_version or "backfill",
        similar_cases=[],
    )
