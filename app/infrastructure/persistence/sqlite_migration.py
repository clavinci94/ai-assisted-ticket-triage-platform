import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import Boolean, DateTime, create_engine, delete, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.infrastructure.persistence.db import Base, _normalize_database_url
from app.infrastructure.persistence.models import TicketEventModel, TicketRecordModel


@dataclass(frozen=True)
class MigrationStats:
    source_tickets: int
    source_events: int
    migrated_tickets: int
    migrated_events: int


def migrate_sqlite_to_database(
    source_path: str | Path,
    target_database_url: str,
    replace: bool = False,
) -> MigrationStats:
    source_db_path = Path(source_path).expanduser().resolve()
    if not source_db_path.exists():
        raise FileNotFoundError(f"SQLite source database not found: {source_db_path}")

    normalized_target_url = _normalize_database_url(target_database_url.strip())
    if not normalized_target_url:
        raise ValueError("Target database URL is required")

    source_connection = sqlite3.connect(source_db_path)
    source_connection.row_factory = sqlite3.Row

    try:
        ticket_rows = _fetch_rows(source_connection, "tickets")
        event_rows = _fetch_rows(source_connection, "ticket_events")
    finally:
        source_connection.close()

    target_engine = create_engine(normalized_target_url)
    try:
        Base.metadata.create_all(bind=target_engine)

        with Session(target_engine) as session:
            if replace:
                session.execute(delete(TicketEventModel))
                session.execute(delete(TicketRecordModel))
                session.flush()

            migrated_tickets = _upsert_rows(session, TicketRecordModel, ticket_rows)
            migrated_events = _upsert_rows(session, TicketEventModel, event_rows)
            session.commit()

            if target_engine.dialect.name == "postgresql":
                _reset_postgres_event_sequence(session)

            session.commit()
    except OperationalError as error:
        raise RuntimeError(_build_connection_error_message(normalized_target_url, error)) from error
    finally:
        target_engine.dispose()

    return MigrationStats(
        source_tickets=len(ticket_rows),
        source_events=len(event_rows),
        migrated_tickets=migrated_tickets,
        migrated_events=migrated_events,
    )


def _fetch_rows(connection: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    # table_name is never user-supplied — callers pass hard-coded literals
    # ("tickets", "ticket_events"). Interpolation is required because SQLite
    # does not support parameter binding for table identifiers.
    cursor = connection.execute(f"SELECT * FROM {table_name}")  # nosec B608
    return [dict(row) for row in cursor.fetchall()]


def _upsert_rows(session: Session, model, rows: list[dict[str, Any]]) -> int:
    migrated = 0

    for row in rows:
        payload = _coerce_row(model, row)
        instance = session.get(model, payload["id"])

        if instance is None:
            session.add(model(**payload))
        else:
            for key, value in payload.items():
                setattr(instance, key, value)

        migrated += 1

    session.flush()
    return migrated


def _coerce_row(model, row: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    for column in model.__table__.columns:
        value = row.get(column.name)

        if isinstance(column.type, DateTime):
            value = _coerce_datetime(value)
        elif isinstance(column.type, Boolean):
            value = _coerce_boolean(value)

        payload[column.name] = value

    return payload


def _coerce_datetime(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None

    if isinstance(value, datetime):
        return value

    normalized = str(value).strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    return datetime.fromisoformat(normalized)


def _coerce_boolean(value: Any) -> bool | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y"}:
        return True
    if normalized in {"0", "false", "f", "no", "n"}:
        return False

    return bool(value)


def _reset_postgres_event_sequence(session: Session) -> None:
    session.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('ticket_events', 'id'),
                COALESCE((SELECT MAX(id) FROM ticket_events), 1),
                EXISTS(SELECT 1 FROM ticket_events)
            )
            """
        )
    )


def _build_connection_error_message(database_url: str, error: OperationalError) -> str:
    host = urlparse(database_url).hostname or ""
    if host.startswith("dpg-") and "." not in host:
        return (
            "Could not connect to the target database. The configured Render hostname looks like an Internal Database URL, "
            "which only works from services running inside Render. If you run this migration from your laptop, switch "
            "to the Render External Database URL in DATABASE_URL or pass it via --target-database-url."
        )

    return f"Could not connect to the target database: {error}"
