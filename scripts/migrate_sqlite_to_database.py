#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.infrastructure.persistence.sqlite_migration import migrate_sqlite_to_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate the local SQLite triage database into another SQLAlchemy-compatible database.",
    )
    parser.add_argument(
        "--source",
        default="triage.db",
        help="Path to the source SQLite database. Defaults to triage.db.",
    )
    parser.add_argument(
        "--target-database-url",
        default=None,
        help="Target database URL. Defaults to the DATABASE_URL environment variable.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing target data before importing tickets and events.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    target_database_url = args.target_database_url or os.getenv("DATABASE_URL")
    if not target_database_url:
        print("Missing target database URL. Set DATABASE_URL or pass --target-database-url.", file=sys.stderr)
        return 1

    print(f"Starting migration from {args.source}", flush=True)
    print("Connecting to target database", flush=True)

    stats = migrate_sqlite_to_database(
        source_path=args.source,
        target_database_url=target_database_url,
        replace=args.replace,
    )

    print(f"Migrated {stats.migrated_tickets}/{stats.source_tickets} tickets", flush=True)
    print(f"Migrated {stats.migrated_events}/{stats.source_events} ticket events", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
