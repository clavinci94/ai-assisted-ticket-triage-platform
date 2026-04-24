from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.infrastructure.persistence.db import Base
from app.infrastructure.persistence.models import TicketEventModel, TicketRecordModel
from app.infrastructure.persistence.sqlite_migration import (
    _build_connection_error_message,
    migrate_sqlite_to_database,
)


def test_migrate_sqlite_to_database_copies_tickets_and_events(tmp_path: Path):
    source_path = tmp_path / "source.db"
    target_path = tmp_path / "target.db"

    source_engine = create_engine(f"sqlite:///{source_path}")
    Base.metadata.create_all(bind=source_engine)

    with Session(source_engine) as session:
        session.add(
            TicketRecordModel(
                id="ticket-1",
                title="Login outage",
                description="Users cannot log in.",
                reporter="claudio",
                source="internal",
                department="Bank-IT Support",
                category="bug",
                priority="high",
                team="it-support-team",
                assignee="claudio",
                due_at=datetime(2026, 4, 13, 8, 30, 0),
                tags='["incident","login"]',
                sla_breached=False,
                status="triaged",
                predicted_category="bug",
                category_confidence=0.75,
                predicted_priority="high",
                priority_confidence=0.7,
                summary="Login issue erkannt.",
                suggested_team="it-support-team",
                suggested_department="Bank-IT Support",
                next_step="Logs prüfen.",
                rationale="Produktionsstörung mit hoher Relevanz.",
                model_version="litellm-azure_ai/gpt-oss-120b",
                analyzed_at=datetime(2026, 4, 13, 8, 0, 0),
                final_category="bug",
                final_priority="high",
                final_team="it-support-team",
                accepted_ai_suggestion=True,
                review_comment="Sieht korrekt aus.",
                reviewed_by="claudio",
                assigned_team="incident-response-team",
                assigned_by="claudio",
                assignment_note="Sofort übernehmen.",
            )
        )
        session.add(
            TicketEventModel(
                id=42,
                ticket_id="ticket-1",
                event_type="ticket_created",
                actor="claudio",
                summary="Ticket erstellt",
                details="Quelle: internal",
                created_at=datetime(2026, 4, 13, 8, 0, 0),
            )
        )
        session.commit()

    stats = migrate_sqlite_to_database(
        source_path=source_path,
        target_database_url=f"sqlite:///{target_path}",
    )

    assert stats.source_tickets == 1
    assert stats.source_events == 1
    assert stats.migrated_tickets == 1
    assert stats.migrated_events == 1

    target_engine = create_engine(f"sqlite:///{target_path}")
    with Session(target_engine) as session:
        ticket = session.get(TicketRecordModel, "ticket-1")
        event = session.get(TicketEventModel, 42)

        assert ticket is not None
        assert ticket.title == "Login outage"
        assert ticket.department == "Bank-IT Support"
        assert ticket.accepted_ai_suggestion is True
        assert event is not None
        assert event.ticket_id == "ticket-1"
        assert event.summary == "Ticket erstellt"


def test_build_connection_error_message_explains_render_internal_url():
    error = OperationalError("statement", {}, Exception("dns failed"))

    message = _build_connection_error_message(
        "postgresql+psycopg://user:password@dpg-example/triage",
        error,
    )

    assert "Internal Database URL" in message
    assert "External Database URL" in message
