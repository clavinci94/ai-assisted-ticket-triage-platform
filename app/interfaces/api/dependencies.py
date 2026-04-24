from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from app.application.ports.similar_tickets_port import SimilarTicketsPort
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


def get_similar_tickets(request: Request) -> SimilarTicketsPort:
    """Pull the process-wide SimilarTicketsPort singleton off app.state.

    The adapter is built once during ``create_app()`` so every request
    shares the same fitted index — building TF-IDF per request would be
    wasteful and non-deterministic under load.
    """
    return request.app.state.similar_tickets
