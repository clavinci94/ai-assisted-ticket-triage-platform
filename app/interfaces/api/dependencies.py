from collections.abc import Generator

from sqlalchemy.orm import Session

from app.infrastructure.persistence.db import SessionLocal
from app.infrastructure.persistence.sqlite_ticket_repository import SQLiteTicketRepository


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_ticket_repository(
    session: Session,
) -> SQLiteTicketRepository:
    return SQLiteTicketRepository(session=session)
