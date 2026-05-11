import os
from collections.abc import Generator

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.infrastructure.persistence.db import SessionLocal
from app.infrastructure.persistence.sqlite_ticket_repository import SQLiteTicketRepository

ADMIN_API_KEY_HEADER = "X-API-Key"


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


def require_admin_api_key(request: Request) -> None:
    """Hard gate for /admin/* endpoints.

    Reads ``ADMIN_API_KEY`` from the environment at request time. If it
    is set, requests must carry a matching ``X-API-Key`` header to
    proceed. If it is unset, requests are refused with HTTP 503 — the
    secure default — unless ``ADMIN_ALLOW_UNAUTHENTICATED=1`` is also
    set (for local dev and the test suite).
    """

    expected = os.getenv("ADMIN_API_KEY")
    allow_unauth = os.getenv("ADMIN_ALLOW_UNAUTHENTICATED", "").lower() in {
        "1",
        "true",
        "yes",
    }

    if not expected:
        if allow_unauth:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Admin endpoints are not configured. Set ADMIN_API_KEY in "
                "the environment (or ADMIN_ALLOW_UNAUTHENTICATED=1 for local dev)."
            ),
        )

    provided = request.headers.get(ADMIN_API_KEY_HEADER)
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key.",
        )
