"""Unit tests for TfidfSimilarTicketsAdapter.

Each test spins up an isolated in-memory SQLite database so the retrieval
layer can be exercised against real SQLAlchemy models without touching the
developer's triage.db.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.ai.tfidf_similar_tickets import TfidfSimilarTicketsAdapter
from app.infrastructure.persistence.db import Base
from app.infrastructure.persistence.models import TicketRecordModel


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal


def _seed(session_factory, tickets):
    session: Session = session_factory()
    try:
        for t in tickets:
            session.add(TicketRecordModel(**t))
        session.commit()
    finally:
        session.close()


def _reviewed(
    ticket_id, title, description, *, dept="Bank-IT Support", team="it-support-team", category="support"
):
    return {
        "id": ticket_id,
        "title": title,
        "description": description,
        "reporter": "tester",
        "source": "internal",
        "department": dept,
        "status": "reviewed",
        "reviewed_by": "operator",  # retrieval corpus = human-reviewed only
        "final_team": team,
        "final_category": category,
        "sla_breached": False,
    }


def test_returns_empty_list_before_first_rebuild(session_factory):
    adapter = TfidfSimilarTicketsAdapter(session_factory)
    assert adapter.find_similar("Login geht nicht") == []


def test_rebuild_below_minimum_corpus_disables_retrieval(session_factory):
    _seed(session_factory, [_reviewed("t1", "VPN defekt", "Citrix verbindet nicht")])
    adapter = TfidfSimilarTicketsAdapter(session_factory)
    indexed = adapter.rebuild()

    assert indexed == 1
    assert adapter.find_similar("VPN") == []  # graceful degradation


def test_rebuild_ignores_tickets_without_review_decision(session_factory):
    _seed(
        session_factory,
        [
            {
                "id": "t1",
                "title": "Unreviewed bug",
                "description": "x",
                "reporter": "x",
                "source": "internal",
                "department": "Bank-IT Support",
                "status": "new",
                "sla_breached": False,
                # no final_department → excluded
            },
            _reviewed("t2", "VPN defekt", "Citrix hängt"),
            _reviewed("t3", "Passwort reset", "User kann sich nicht anmelden"),
            _reviewed("t4", "Drucker offline", "Kein Papier und kein Netzwerk"),
        ],
    )
    adapter = TfidfSimilarTicketsAdapter(session_factory)
    indexed = adapter.rebuild()

    assert indexed == 3  # only the three reviewed tickets


def test_find_similar_returns_most_relevant_reviewed_ticket(session_factory):
    _seed(
        session_factory,
        [
            _reviewed(
                "vpn-1",
                "VPN-Zugang defekt",
                "Citrix Workspace meldet Verbindungsfehler am Windows-Rechner.",
                dept="Bank-IT Support",
                team="network-team",
            ),
            _reviewed(
                "pw-1",
                "Passwort-Reset SAP",
                "User kann sich nicht in SAP-GUI einloggen.",
                dept="IT-User-Services",
                team="user-services",
            ),
            _reviewed(
                "print-1",
                "Drucker offline",
                "Etagendrucker reagiert nicht.",
                dept="Bank-IT Support",
                team="hardware-team",
            ),
            _reviewed(
                "vpn-2",
                "Citrix startet nicht",
                "VPN-Client schlägt auf Mac fehl, Fehler 500.",
                dept="Bank-IT Support",
                team="network-team",
            ),
        ],
    )

    adapter = TfidfSimilarTicketsAdapter(session_factory, min_similarity=0.0)
    adapter.rebuild()

    hits = adapter.find_similar("Citrix VPN funktioniert nicht, Verbindungsfehler", top_k=2)

    assert len(hits) == 2
    # The VPN tickets should dominate the top-2; password and printer should not.
    top_ids = {case.ticket_id for case in hits}
    assert top_ids.issubset({"vpn-1", "vpn-2"})
    # Metadata must be the reviewed routing, not the raw ticket fields.
    assert hits[0].final_department == "Bank-IT Support"
    assert hits[0].final_team == "network-team"
    assert 0.0 <= hits[0].similarity_score <= 1.0


def test_find_similar_drops_matches_below_min_similarity(session_factory):
    _seed(
        session_factory,
        [
            _reviewed("a", "Kaffeemaschine defekt", "Küche, erste Etage"),
            _reviewed("b", "Parkplatz-Schranke klemmt", "Besucherbereich"),
            _reviewed("c", "Fahrstuhl wartet", "Turm B"),
        ],
    )
    adapter = TfidfSimilarTicketsAdapter(session_factory, min_similarity=0.95)
    adapter.rebuild()

    # A totally unrelated query should not clear the 0.95 bar.
    assert adapter.find_similar("SQL Performance Tuning") == []


def test_rebuild_is_idempotent_and_reflects_new_tickets(session_factory):
    _seed(
        session_factory,
        [
            _reviewed("1", "A", "aaa"),
            _reviewed("2", "B", "bbb"),
            _reviewed("3", "C", "ccc"),
        ],
    )
    adapter = TfidfSimilarTicketsAdapter(session_factory)
    assert adapter.rebuild() == 3

    _seed(session_factory, [_reviewed("4", "D", "ddd")])
    assert adapter.rebuild() == 4
