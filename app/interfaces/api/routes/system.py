from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.infrastructure.persistence.db import engine

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
        raise HTTPException(status_code=503, detail=f"database unreachable: {error}") from error

    return {"status": "ready"}
