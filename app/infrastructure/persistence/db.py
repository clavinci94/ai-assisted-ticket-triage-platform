from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./triage.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_ticket_department_column() -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "tickets" not in inspector.get_table_names():
        return

    columns = [column["name"] for column in inspector.get_columns("tickets")]
    if "department" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE tickets ADD COLUMN department VARCHAR(100) NOT NULL DEFAULT 'Bank-IT Support'"
            )
        )


def ensure_ticket_suggested_department_column() -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "tickets" not in inspector.get_table_names():
        return

    columns = [column["name"] for column in inspector.get_columns("tickets")]
    if "suggested_department" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE tickets ADD COLUMN suggested_department VARCHAR(100)"
            )
        )
