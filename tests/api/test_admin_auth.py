"""Verify the admin API-key gate (require_admin_api_key dependency).

The dependency reads env vars at request time, so we can flip the gate
mid-test without recreating the app.
"""

import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_unauthenticated_returns_503_when_neither_key_nor_allow_flag(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_ALLOW_UNAUTHENTICATED", raising=False)
    response = client.post("/admin/seed-demo")
    assert response.status_code == 503
    assert "ADMIN_API_KEY" in response.json()["detail"]


def test_admin_unauthenticated_passes_with_allow_flag(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    monkeypatch.setenv("ADMIN_ALLOW_UNAUTHENTICATED", "1")
    response = client.post("/admin/seed-demo")
    # 200 happy path or 500 if seed fails for other reasons — either way,
    # the gate was passed.
    assert response.status_code != 503
    assert response.status_code != 401


def test_admin_rejects_missing_header_when_key_configured(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "s3cr3t")
    monkeypatch.delenv("ADMIN_ALLOW_UNAUTHENTICATED", raising=False)
    response = client.post("/admin/seed-demo")
    assert response.status_code == 401


def test_admin_rejects_wrong_header_when_key_configured(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "s3cr3t")
    monkeypatch.delenv("ADMIN_ALLOW_UNAUTHENTICATED", raising=False)
    response = client.post("/admin/seed-demo", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_admin_accepts_matching_header_when_key_configured(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "s3cr3t")
    monkeypatch.delenv("ADMIN_ALLOW_UNAUTHENTICATED", raising=False)
    response = client.post("/admin/seed-demo", headers={"X-API-Key": "s3cr3t"})
    assert response.status_code != 401
    assert response.status_code != 503


def teardown_module(module):  # noqa: ARG001
    # Restore the conftest default so the rest of the suite stays open.
    os.environ.setdefault("ADMIN_ALLOW_UNAUTHENTICATED", "1")
