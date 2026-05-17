import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.application.use_cases.analytics_cache import analytics_cache
from app.application.use_cases.backfill_prioritization import (
    BackfillPrioritizationUseCase,
)
from app.application.use_cases.read_cache import (
    invalidate_ticket_reads,
    tickets_list_cache,
    workbench_cache,
)
from app.application.use_cases.retrain_model import RetrainModelUseCase
from app.infrastructure.ai.policy_based_prioritizer import PolicyBasedPrioritizer
from app.infrastructure.ai.tfidf_similar_tickets import TfidfSimilarTicketsAdapter
from app.infrastructure.seeding.demo_tickets import seed as seed_demo_tickets
from app.interfaces.api.dependencies import get_similar_tickets, require_admin_api_key
from app.interfaces.api.schemas.admin_schemas import (
    BackfillPrioritizationResponse,
    RebuildRagResponse,
    RetrainResponse,
    SeedDemoResponse,
)

logger = logging.getLogger(__name__)

# Every route on this router goes through ``require_admin_api_key``. The
# dependency reads ADMIN_API_KEY from the environment per-request, so
# tests can flip the gate by setting/unsetting the env var.
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_key)],
)

SimilarTicketsDep = Annotated[SimilarTicketsPort, Depends(get_similar_tickets)]


@router.post("/retrain", response_model=RetrainResponse)
def retrain_model() -> RetrainResponse:
    use_case = RetrainModelUseCase()

    try:
        model_path = use_case.execute()
    except Exception as exc:
        logger.exception("retrain failed")
        raise HTTPException(status_code=500, detail="Model retraining failed.") from exc

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
        logger.exception("RAG rebuild failed")
        raise HTTPException(status_code=500, detail="Retrieval index rebuild failed.") from exc

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
    purge_test_pollution: bool = Query(
        default=True,
        description=(
            "Delete rows whose title matches a known pytest fixture prefix "
            "(WB-PAGE-CLAUDIO, WB-VIEWS-CLAUDIO, Workflow * Test)."
        ),
    ),
    dedupe_non_demo: bool = Query(
        default=True,
        description=(
            "Keep only one row per title for non-demo tickets (e.g. dozens of "
            "duplicated 'Password reset request' rows from past manual tests)."
        ),
    ),
) -> SeedDemoResponse:
    """Populate the database with the curated demo ticket corpus for the RAG demo.

    Safe to call repeatedly: with ``replace=true`` (default) it wipes any
    existing DEMO-* rows before reinserting, so you always end up with the
    canonical catalog. With ``purge_test_pollution`` and ``dedupe_non_demo``
    (also defaulting on) it additionally cleans up test fixtures and duplicate
    titles that may have leaked into the DB from past pytest runs or manual
    triage attempts. Rebuilds the retrieval index afterwards so the next
    triage request sees the new corpus immediately.
    """
    try:
        result = seed_demo_tickets(
            replace=replace,
            purge_test_pollution=purge_test_pollution,
            dedupe_non_demo=dedupe_non_demo,
        )
    except Exception as exc:  # pragma: no cover — surfaced as HTTP error
        logger.exception("seed-demo failed")
        raise HTTPException(status_code=500, detail="Seeding the demo corpus failed.") from exc

    try:
        indexed = similar_tickets.rebuild()
    except Exception:
        indexed = None

    analytics_cache.invalidate()
    invalidate_ticket_reads()

    return SeedDemoResponse(
        status=result["status"],
        deleted=result["deleted"],
        inserted=result["inserted"],
        inserted_demo=result.get("inserted_demo", 0),
        inserted_historical=result.get("inserted_historical", 0),
        purged_test_pollution=result.get("purged_test_pollution", 0),
        deduplicated=result.get("deduplicated", 0),
        skipped_existing=result["skipped_existing"],
        total_demo_records=result["total_demo_records"],
        total_historical_records=result.get("total_historical_records", 0),
        indexed_tickets=indexed,
        message=(
            f"Seeded {result.get('inserted_demo', 0)} demo + "
            f"{result.get('inserted_historical', 0)} historical tickets "
            f"(removed {result['deleted']}, skipped {result['skipped_existing']}, "
            f"purged {result.get('purged_test_pollution', 0)} test-fixture rows, "
            f"deduped {result.get('deduplicated', 0)} non-seed duplicates). "
            f"RAG index now holds {indexed if indexed is not None else 'n/a'} reviewed tickets."
        ),
    )


@router.post(
    "/backfill-prioritization",
    response_model=BackfillPrioritizationResponse,
)
def backfill_prioritization(
    similar_tickets: SimilarTicketsDep,
    force: bool = Query(
        default=False,
        description=(
            "If true, re-score every ticket regardless of its current "
            "prioritisation. Use after editing triage_policy.yaml to roll "
            "the new rules over existing tickets. Defaults to false — "
            "idempotent backfill mode that only touches NULL rows."
        ),
    ),
) -> BackfillPrioritizationResponse:
    """Run the KE prioritizer over tickets that need scoring.

    Default mode (``force=false``): synthesises inputs from each row's
    existing classification fields and persists a fresh
    ``Prioritization`` for every ticket where ``impact_score IS NULL``.
    Idempotent — already-scored tickets are skipped.

    Force mode (``force=true``): re-scores every ticket in the table
    against the *current* policy. Used after a policy change so existing
    tickets pick up the new rule set.
    """

    try:
        use_case = BackfillPrioritizationUseCase(
            prioritizer=PolicyBasedPrioritizer(),
            similar_tickets=similar_tickets,
        )
        result = use_case.execute(force=force)
    except Exception as exc:  # pragma: no cover — surfaced as HTTP error
        logger.exception("prioritization backfill failed")
        raise HTTPException(status_code=500, detail="Prioritization backfill failed.") from exc

    analytics_cache.invalidate()
    invalidate_ticket_reads()

    return BackfillPrioritizationResponse(
        status="ok",
        candidates=result.candidates,
        prioritized=result.prioritized,
        skipped=result.skipped,
        failed=result.failed,
        message=(
            f"Backfilled {result.prioritized} of {result.candidates} tickets "
            f"({result.failed} failed, {result.skipped} skipped)."
        ),
    )


@router.get("/_diagnostics/cache")
def cache_diagnostics() -> dict:
    """Read-only probe — reports cache state + process id.

    Hit twice from the same client; if ``process_id`` differs between
    calls the service is running multiple worker processes (the
    in-memory caches don't help in that topology). If ``process_id``
    matches but ``entries`` stays 0 across calls, the cache logic is
    broken. If ``entries`` grows, the cache works.
    """

    return {
        "process_id": os.getpid(),
        "tickets_list_cache": {
            "id": id(tickets_list_cache),
            "ttl_seconds": tickets_list_cache._ttl,
            "entry_count": len(tickets_list_cache._entries),
            "keys": [repr(k)[:80] for k in tickets_list_cache._entries],
        },
        "workbench_cache": {
            "id": id(workbench_cache),
            "ttl_seconds": workbench_cache._ttl,
            "entry_count": len(workbench_cache._entries),
        },
        "analytics_cache": {
            "id": id(analytics_cache),
            "has_value": analytics_cache._value is not None,
            "ttl_seconds": analytics_cache._ttl,
        },
    }
