"""Unit tests for the RagAssistedClassifier decorator.

The decorator's job is narrow: fetch similar cases, pass them through to
the inner classifier, and make sure they survive into the returned
TriageAnalysis. We exercise that contract without hitting any LLM API.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.application.ports.classifier_port import ClassifierPort
from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.domain.enums.ticket_status import TicketStatus
from app.infrastructure.ai.rag_assisted_classifier import RagAssistedClassifier


class _RecordingClassifier(ClassifierPort):
    """Inner stand-in. Records the similar_cases it was called with so tests
    can verify the decorator forwarded them correctly."""

    def __init__(self, *, attach_cases: bool = False) -> None:
        self.received_cases: list[SimilarCase] | None = None
        self._attach_cases = attach_cases

    def analyze(self, ticket, similar_cases=None):
        self.received_cases = list(similar_cases) if similar_cases is not None else None
        return TriageAnalysis(
            predicted_category=TicketCategory.SUPPORT,
            category_confidence=0.9,
            predicted_priority=TicketPriority.MEDIUM,
            priority_confidence=0.8,
            summary="stub summary",
            suggested_team="it-support-team",
            suggested_department="Bank-IT Support",
            next_step="prüfen",
            rationale="stub",
            model_version="stub",
            analyzed_at=datetime.now(UTC),
            similar_cases=list(similar_cases or []) if self._attach_cases else [],
        )


class _FakeSimilarTickets(SimilarTicketsPort):
    def __init__(self, corpus: list[SimilarCase] | None = None, raise_on_find: bool = False) -> None:
        self._corpus = corpus or []
        self._raise = raise_on_find
        self.find_calls: list[tuple[str, int]] = []

    def find_similar(self, text, top_k=3):
        if self._raise:
            raise RuntimeError("retrieval down")
        self.find_calls.append((text, top_k))
        return list(self._corpus[:top_k])

    def rebuild(self):
        return len(self._corpus)


@pytest.fixture()
def ticket() -> Ticket:
    return Ticket(
        id="T-1",
        title="VPN defekt",
        description="Citrix startet nicht",
        reporter="operator",
        source="internal",
        status=TicketStatus.NEW,
        department="Bank-IT Support",
    )


@pytest.fixture()
def corpus_case() -> SimilarCase:
    return SimilarCase(
        ticket_id="T-older",
        title="Citrix fehlerhaft",
        final_department="Bank-IT Support",
        final_category="support",
        final_team="network-team",
        similarity_score=0.82,
    )


def test_forwards_fetched_cases_to_inner_classifier(ticket, corpus_case):
    inner = _RecordingClassifier()
    retrieval = _FakeSimilarTickets(corpus=[corpus_case])
    classifier = RagAssistedClassifier(inner=inner, similar_tickets=retrieval)

    result = classifier.analyze(ticket)

    assert inner.received_cases == [corpus_case]
    assert retrieval.find_calls == [("VPN defekt Citrix startet nicht", 3)]
    assert result.similar_cases == [corpus_case]


def test_preserves_cases_when_inner_already_attached_them(ticket, corpus_case):
    inner = _RecordingClassifier(attach_cases=True)
    retrieval = _FakeSimilarTickets(corpus=[corpus_case])
    classifier = RagAssistedClassifier(inner=inner, similar_tickets=retrieval)

    result = classifier.analyze(ticket)

    # Inner returned them, decorator must not duplicate.
    assert len(result.similar_cases) == 1
    assert result.similar_cases[0].ticket_id == "T-older"


def test_caller_supplied_cases_bypass_retrieval(ticket):
    inner = _RecordingClassifier()
    retrieval = _FakeSimilarTickets(corpus=[])
    classifier = RagAssistedClassifier(inner=inner, similar_tickets=retrieval)

    provided = [
        SimilarCase(
            ticket_id="T-override",
            title="Manually injected",
            final_department="Bank-IT Support",
            final_category="support",
            final_team=None,
            similarity_score=0.99,
        )
    ]
    result = classifier.analyze(ticket, similar_cases=provided)

    assert retrieval.find_calls == []  # no retrieval fired
    assert result.similar_cases == provided
    assert inner.received_cases == provided


def test_empty_corpus_produces_empty_cases(ticket):
    inner = _RecordingClassifier()
    retrieval = _FakeSimilarTickets(corpus=[])
    classifier = RagAssistedClassifier(inner=inner, similar_tickets=retrieval)

    result = classifier.analyze(ticket)

    assert result.similar_cases == []
    assert inner.received_cases == []


def test_retrieval_failure_falls_back_to_plain_classification(ticket):
    inner = _RecordingClassifier()
    retrieval = _FakeSimilarTickets(raise_on_find=True)
    classifier = RagAssistedClassifier(inner=inner, similar_tickets=retrieval)

    # Must not raise — retrieval errors are swallowed.
    result = classifier.analyze(ticket)

    assert result.similar_cases == []
    assert inner.received_cases == []  # inner got empty context, not None


def test_top_k_is_forwarded_to_retrieval(ticket):
    inner = _RecordingClassifier()
    retrieval = _FakeSimilarTickets(corpus=[])
    classifier = RagAssistedClassifier(inner=inner, similar_tickets=retrieval, top_k=7)

    classifier.analyze(ticket)

    assert retrieval.find_calls == [("VPN defekt Citrix startet nicht", 7)]
