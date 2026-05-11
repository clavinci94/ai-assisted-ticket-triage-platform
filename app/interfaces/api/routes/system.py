import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.infrastructure.persistence.db import engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — no downstream dependencies."""
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str]:
    """Readiness probe — verifies the database is reachable."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:  # pragma: no cover — covered by integration test w/ bad DSN
        # Never echo the connection error verbatim — it can contain DSN credentials.
        logger.exception("database readiness check failed")
        raise HTTPException(status_code=503, detail="Database unreachable.") from error

    return {"status": "ready"}
