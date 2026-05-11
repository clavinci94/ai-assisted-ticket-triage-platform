"""Pytest bootstrap: isolate the test DB and put project root on sys.path.

Tests previously inherited the process-level ``DATABASE_URL`` (or fell back
to ``sqlite:///./triage.db``), which meant pytest e2e runs leaked rows like
``WB-VIEWS-CLAUDIO Kritisch`` and ``Workflow Close Test`` into the actual
demo / production database. We now redirect every test run to a throwaway
SQLite file in a session-scoped tmp dir.

Set ``KEEP_TEST_DB=1`` to inspect the file after a run; it defaults to being
deleted at session end.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)

if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Isolate the test database BEFORE any ``from app...`` import resolves —
# app.infrastructure.persistence.db reads DATABASE_URL at import time.
_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="triage-tests-"))
_TEST_DB_PATH = _TEST_DB_DIR / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    if os.environ.get("KEEP_TEST_DB") == "1":
        return
    shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)
