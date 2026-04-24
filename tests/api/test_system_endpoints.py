"""Integration tests for health/readiness probes and middleware wiring."""

from __future__ import annotations

import importlib
import os
from unittest.mock import patch

from fastapi.testclient import TestClient


def _client_with_app():
    """Import the app fresh so module-level create_app() re-runs with the current env."""
    from app.interfaces.api import app as app_module

    importlib.reload(app_module)
    return TestClient(app_module.app)


def test_health_is_public_and_returns_ok():
    client = _client_with_app()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_ready_when_db_reachable():
    client = _client_with_app()
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_returns_503_when_db_unreachable():
    from app.interfaces.api.routes import system as system_routes

    class _BrokenEngine:
        def connect(self):
            raise RuntimeError("simulated DB outage")

    with patch.object(system_routes, "engine", _BrokenEngine()):
        client = _client_with_app()
        response = client.get("/ready")

    assert response.status_code == 503
    assert "database unreachable" in response.json()["detail"].lower()


def test_request_id_is_echoed_in_response_header():
    client = _client_with_app()
    response = client.get("/health", headers={"X-Request-ID": "test-correlation-42"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-correlation-42"


def test_request_id_is_generated_when_missing():
    client = _client_with_app()
    response = client.get("/health")

    assert response.status_code == 200
    assert len(response.headers.get("X-Request-ID", "")) >= 8


def test_api_key_middleware_is_noop_when_unset():
    # No API_KEY configured → every endpoint should work without a header.
    if "API_KEY" in os.environ:
        del os.environ["API_KEY"]

    client = _client_with_app()
    response = client.get("/tickets")

    # /tickets should answer (possibly with data, possibly empty) — NOT 401.
    assert response.status_code != 401


def test_api_key_middleware_rejects_missing_key():
    os.environ["API_KEY"] = "top-secret"
    try:
        client = _client_with_app()
        response = client.get("/tickets")
        assert response.status_code == 401
        assert response.json()["detail"].lower().startswith("invalid")
    finally:
        del os.environ["API_KEY"]


def test_api_key_middleware_accepts_valid_key():
    os.environ["API_KEY"] = "top-secret"
    try:
        client = _client_with_app()
        response = client.get("/tickets", headers={"X-API-Key": "top-secret"})
        assert response.status_code != 401
    finally:
        del os.environ["API_KEY"]


def test_api_key_middleware_keeps_health_and_docs_public():
    os.environ["API_KEY"] = "top-secret"
    try:
        client = _client_with_app()
        assert client.get("/health").status_code == 200
        assert client.get("/openapi.json").status_code == 200
    finally:
        del os.environ["API_KEY"]
