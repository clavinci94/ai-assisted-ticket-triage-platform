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

from app.infrastructure.seeding.demo_tickets import DEMO_TICKETS, seed  # noqa: E402


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete demo tickets (prefix DEMO-) before seeding.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    result = seed(replace=args.replace)
    if args.replace:
        print(f"removed {result['deleted']} previously seeded demo tickets")
    print(
        f"seeded {result['inserted']} demo tickets "
        f"(skipped {result['skipped_existing']} that already existed, "
        f"{len(DEMO_TICKETS)} total in catalog)"
    )
