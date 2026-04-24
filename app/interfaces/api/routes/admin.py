from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.application.use_cases.retrain_model import RetrainModelUseCase
from app.infrastructure.ai.tfidf_similar_tickets import TfidfSimilarTicketsAdapter
from app.infrastructure.seeding.demo_tickets import seed as seed_demo_tickets
from app.interfaces.api.dependencies import get_similar_tickets
from app.interfaces.api.schemas.admin_schemas import (
    RebuildRagResponse,
    RetrainResponse,
    SeedDemoResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])

SimilarTicketsDep = Annotated[SimilarTicketsPort, Depends(get_similar_tickets)]


@router.post("/retrain", response_model=RetrainResponse)
def retrain_model() -> RetrainResponse:
    use_case = RetrainModelUseCase()

    try:
        model_path = use_case.execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RetrainResponse(
        status="success",
        message="Model retrained successfully.",
        model_path=str(model_path),
    )


@router.post("/rebuild-rag", response_model=RebuildRagResponse)
def rebuild_rag_index(similar_tickets: SimilarTicketsDep) -> RebuildRagResponse:
    """Refit the retrieval index against the current reviewed-ticket corpus.

    Call this after bulk-importing historical tickets or on a schedule if
    you want the retrieval layer to reflect very recent review decisions
    without restarting the process.
    """
    try:
        indexed = similar_tickets.rebuild()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"rebuild failed: {exc}") from exc

    minimum = getattr(similar_tickets, "MIN_CORPUS_SIZE", TfidfSimilarTicketsAdapter.MIN_CORPUS_SIZE)
    if indexed < minimum:
        message = (
            f"Index rebuilt but disabled — only {indexed} reviewed tickets in corpus, "
            f"need at least {minimum} for retrieval to be meaningful."
        )
    else:
        message = f"Index rebuilt with {indexed} reviewed tickets."

    return RebuildRagResponse(
        status="ok",
        indexed_tickets=indexed,
        minimum_corpus_size=minimum,
        message=message,
    )


@router.post("/seed-demo", response_model=SeedDemoResponse)
def seed_demo_corpus(
    similar_tickets: SimilarTicketsDep,
    replace: bool = Query(
        default=True,
        description="Delete existing DEMO-* rows before inserting. Default true so the endpoint is idempotent.",
    ),
) -> SeedDemoResponse:
    """Populate the database with ~20 reviewed demo tickets for the RAG demo.

    Safe to call repeatedly: with ``replace=true`` (default) it wipes any
    existing DEMO-* rows before reinserting, so you always end up with the
    canonical catalog. Rebuilds the retrieval index afterwards so the next
    triage request sees the new corpus immediately.
    """
    try:
        result = seed_demo_tickets(replace=replace)
    except Exception as exc:  # pragma: no cover — surfaced as HTTP error
        raise HTTPException(status_code=500, detail=f"seed failed: {exc}") from exc

    try:
        indexed = similar_tickets.rebuild()
    except Exception:
        indexed = None

    return SeedDemoResponse(
        status=result["status"],
        deleted=result["deleted"],
        inserted=result["inserted"],
        skipped_existing=result["skipped_existing"],
        total_demo_records=result["total_demo_records"],
        indexed_tickets=indexed,
        message=(
            f"Seeded {result['inserted']} demo tickets "
            f"(removed {result['deleted']}, skipped {result['skipped_existing']}). "
            f"RAG index now holds {indexed if indexed is not None else 'n/a'} reviewed tickets."
        ),
    )
