"""Verify the per-IP rate limit on LLM-bound endpoints."""

import os

import pytest
from fastapi.testclient import TestClient

# IMPORTANT: set the env var BEFORE importing app, because Limiter reads it
# inside _llm_rate_limit() per-request but slowapi caches behaviour at
# decoration time.
os.environ["LLM_RATE_LIMIT"] = "3/minute"

from app.interfaces.api.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402

PAYLOAD = {"title": "Rate limit smoke test", "description": "Lorem ipsum dolor sit amet."}


@pytest.fixture(autouse=True)
def _reset_limiter_state():
    # slowapi keeps state in-memory between requests; reset between tests so
    # the per-IP counter is clean.
    limiter.reset()
    yield
    limiter.reset()


def test_llm_preview_returns_429_after_limit():
    client = TestClient(app)

    # First N requests under the limit succeed (or fail for unrelated reasons —
    # we don't care about the body here, just that the gate hasn't fired).
    for _ in range(3):
        response = client.post("/tickets/triage/llm/preview", json=PAYLOAD)
        assert response.status_code != 429

    # The (N+1)-th request must be rate-limited.
    response = client.post("/tickets/triage/llm/preview", json=PAYLOAD)
    assert response.status_code == 429
    body = response.json()
    assert "Too many requests" in body["detail"]
    assert response.headers.get("Retry-After") == "30"
