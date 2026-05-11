"""Seed the database with ~20 reviewed demo tickets for the RAG demo.

Thin CLI wrapper around app.infrastructure.seeding.demo_tickets.seed().
The real logic lives in the app package so that both this script and the
HTTP endpoint POST /admin/seed-demo can share it.

Usage::

    # local SQLite (default ./triage.db)
    python scripts/seed_demo_tickets.py

    # against a Render Postgres instance
    DATABASE_URL=postgresql://... python scripts/seed_demo_tickets.py

    # wipe existing seed tickets first
    python scripts/seed_demo_tickets.py --replace
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running the script both as ``python scripts/seed_demo_tickets.py`` (from
# the project root) and as ``python -m scripts.seed_demo_tickets``.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.infrastructure.seeding.demo_tickets import (  # noqa: E402
    DEMO_TICKETS,
    HISTORICAL_TICKETS,
    seed,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete demo tickets (prefix DEMO-) before seeding.",
    )
    parser.add_argument(
        "--no-purge",
        dest="purge_test_pollution",
        action="store_false",
        help=(
            "Skip removing pytest e2e fixtures (WB-PAGE-CLAUDIO, WB-VIEWS-CLAUDIO, "
            "Workflow * Test). Purging is on by default."
        ),
    )
    parser.add_argument(
        "--no-dedupe",
        dest="dedupe_non_demo",
        action="store_false",
        help=(
            "Skip deduplicating non-demo rows that share a title. "
            "Dedupe is on by default."
        ),
    )
    parser.set_defaults(purge_test_pollution=True, dedupe_non_demo=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    result = seed(
        replace=args.replace,
        purge_test_pollution=args.purge_test_pollution,
        dedupe_non_demo=args.dedupe_non_demo,
    )
    if args.replace:
        print(f"removed {result['deleted']} previously seeded rows (DEMO-* + HIST-*)")
    if args.purge_test_pollution:
        print(f"purged {result['purged_test_pollution']} pytest-fixture rows")
    if args.dedupe_non_demo:
        print(f"deduplicated {result['deduplicated']} duplicate non-seed rows")
    print(
        f"seeded {result['inserted_demo']} demo + {result['inserted_historical']} historical tickets "
        f"(skipped {result['skipped_existing']} already-present, "
        f"{len(DEMO_TICKETS)} demo + {len(HISTORICAL_TICKETS)} historical in catalog)"
    )
