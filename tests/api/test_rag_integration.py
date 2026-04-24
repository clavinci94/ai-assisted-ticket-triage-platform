"""End-to-end integration test for the retrieval-augmented triage flow.

The point of this file is to prove that the wiring actually works when all
four layers run together — route → decorator → retrieval → schema. We stub
only the LLM call (so tests don't need network access) and let everything
else hit real SQLAlchemy against an in-memory SQLite database.
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.infrastructure.persistence.db import SessionLocal
from app.infrastructure.persistence.models import TicketRecordModel


class _FakeLlm:
    """Stand-in for LitellmClassifier. Remembers what it was called with so
    we can assert the decorator actually passed the retrieved cases down."""

    def __init__(self) -> None:
        self.last_similar_cases: list[SimilarCase] | None = None

    def analyze(self, ticket, similar_cases=None):
        self.last_similar_cases = list(similar_cases or [])
        return TriageAnalysis(
            predicted_category=TicketCategory.SUPPORT,
            category_confidence=0.88,
            predicted_priority=TicketPriority.MEDIUM,
            priority_confidence=0.75,
            summary="Test-Zusammenfassung",
            suggested_team="it-support-team",
            suggested_department="Bank-IT Support",
            next_step="Prüfen",
            rationale="Begründung",
            model_version="test-llm+rag" if similar_cases else "test-llm",
            analyzed_at=datetime.now(UTC),
            similar_cases=list(similar_cases or []),
        )


@pytest.fixture()
def client(monkeypatch):
    """Build a TestClient with the LLM classifier replaced by _FakeLlm."""
    from app.infrastructure.ai.rag_assisted_classifier import RagAssistedClassifier
    from app.interfaces.api import app as app_module
    from app.interfaces.api.routes import tickets as tickets_routes

    fake = _FakeLlm()

    def _build(similar_tickets):
        return RagAssistedClassifier(inner=fake, similar_tickets=similar_tickets)

    importlib.reload(app_module)
    monkeypatch.setattr(tickets_routes, "_build_rag_classifier", _build)

    test_client = TestClient(app_module.app)
    test_client.fake_llm = fake  # expose for assertions
    yield test_client


def _seed_reviewed_corpus():
    """Insert enough reviewed tickets to push the TF-IDF corpus past the
    MIN_CORPUS_SIZE threshold, with topical variety so retrieval can pick a
    clear winner."""
    session = SessionLocal()
    try:
        # Wipe any tickets left over from a previous run against the same DB.
        session.query(TicketRecordModel).delete()
        session.commit()

        session.add_all(
            [
                TicketRecordModel(
                    id="SEED-001",
                    title="VPN Citrix verbindet nicht",
                    description="Mitarbeiter meldet Verbindungsabbrüche über VPN Citrix Workspace.",
                    reporter="alice",
                    source="internal",
                    department="Bank-IT Support",
                    status="reviewed",
                    reviewed_by="operator",
                    final_category="support",
                    final_priority="high",
                    final_team="network-team",
                    sla_breached=False,
                ),
                TicketRecordModel(
                    id="SEED-002",
                    title="Citrix startet gar nicht",
                    description="Nach Windows-Update schlägt VPN-Login fehl, Fehler 500.",
                    reporter="bob",
                    source="internal",
                    department="Bank-IT Support",
                    status="reviewed",
                    reviewed_by="operator",
                    final_category="support",
                    final_priority="high",
                    final_team="network-team",
                    sla_breached=False,
                ),
                TicketRecordModel(
                    id="SEED-003",
                    title="Passwort-Reset SAP",
                    description="User benötigt neuen Zugang zur SAP-Finanzbuchhaltung.",
                    reporter="carol",
                    source="internal",
                    department="Bank-IT Support",
                    status="reviewed",
                    reviewed_by="operator",
                    final_category="support",
                    final_priority="medium",
                    final_team="user-services",
                    sla_breached=False,
                ),
                TicketRecordModel(
                    id="SEED-004",
                    title="Drucker Etage 3 offline",
                    description="Etagendrucker reagiert nicht, Netzwerkanschluss zeigt keine Verbindung.",
                    reporter="dave",
                    source="internal",
                    department="Bank-IT Support",
                    status="reviewed",
                    reviewed_by="operator",
                    final_category="support",
                    final_priority="low",
                    final_team="hardware-team",
                    sla_breached=False,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


def test_preview_endpoint_enriches_response_with_similar_cases(client):
    _seed_reviewed_corpus()
    # Force a fresh rebuild after seeding.
    assert client.post("/admin/rebuild-rag").status_code == 200

    response = client.post(
        "/tickets/triage/llm/preview",
        json={
            "title": "VPN-Verbindungsfehler über Citrix",
            "description": "Benutzer kann sich nicht über VPN verbinden, Citrix Workspace meldet Fehler.",
            "source": "internal",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert "similar_cases" in body
    similar = body["similar_cases"]
    assert len(similar) > 0

    # The VPN-topic seeds should dominate — network-team examples come first.
    top_ids = {case["ticket_id"] for case in similar}
    assert "SEED-001" in top_ids or "SEED-002" in top_ids

    # And the shape must match what the frontend expects.
    first = similar[0]
    for key in (
        "ticket_id",
        "title",
        "final_department",
        "final_category",
        "final_team",
        "similarity_score",
    ):
        assert key in first

    # Decorator must have forwarded the cases to the (stubbed) LLM.
    assert client.fake_llm.last_similar_cases is not None
    assert len(client.fake_llm.last_similar_cases) == len(similar)


def test_admin_rebuild_reports_corpus_size(client):
    _seed_reviewed_corpus()

    response = client.post("/admin/rebuild-rag")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["indexed_tickets"] == 4
    assert body["minimum_corpus_size"] >= 1


def test_preview_falls_back_gracefully_when_corpus_is_empty(client):
    session = SessionLocal()
    try:
        session.query(TicketRecordModel).delete()
        session.commit()
    finally:
        session.close()

    assert client.post("/admin/rebuild-rag").status_code == 200

    response = client.post(
        "/tickets/triage/llm/preview",
        json={
            "title": "Neue Netzwerkfreigabe",
            "description": "Team benötigt Zugriff auf das gemeinsame Laufwerk.",
            "source": "internal",
        },
    )

    assert response.status_code == 200
    body = response.json()
    # Empty corpus → empty similar_cases list, but the endpoint still works.
    assert body["similar_cases"] == []
    assert client.fake_llm.last_similar_cases == []
