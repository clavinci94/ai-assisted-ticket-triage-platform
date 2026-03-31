from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./triage.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _ensure_ticket_column(column_name: str, ddl: str) -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "tickets" not in inspector.get_table_names():
        return

    columns = [column["name"] for column in inspector.get_columns("tickets")]
    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE tickets ADD COLUMN {ddl}"))


def ensure_ticket_columns() -> None:
    _ensure_ticket_column(
        "department",
        "department VARCHAR(100) NOT NULL DEFAULT 'Bank-IT Support'",
    )
    _ensure_ticket_column(
        "suggested_department",
        "suggested_department VARCHAR(100)",
    )
    _ensure_ticket_column(
        "category",
        "category VARCHAR(50)",
    )
    _ensure_ticket_column(
        "priority",
        "priority VARCHAR(50)",
    )
    _ensure_ticket_column(
        "team",
        "team VARCHAR(100)",
    )
    _ensure_ticket_column(
        "assignee",
        "assignee VARCHAR(100)",
    )
    _ensure_ticket_column(
        "due_at",
        "due_at DATETIME",
    )
    _ensure_ticket_column(
        "tags",
        "tags TEXT",
    )
    _ensure_ticket_column(
        "sla_breached",
        "sla_breached BOOLEAN NOT NULL DEFAULT 0",
    )
