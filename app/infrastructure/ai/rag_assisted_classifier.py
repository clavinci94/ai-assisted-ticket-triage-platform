"""Retrieval-augmented classifier — decorates any ClassifierPort with
examples of past reviewed routing decisions.

The decorator pattern keeps retrieval concerns out of the inner classifier
and preserves the Open/Closed principle: today we wrap the LiteLLM
classifier; tomorrow we could wrap a local model or a different adapter
without touching either side.

Failure mode: if retrieval fails for any reason (DB hiccup, cold index,
empty corpus), we log and fall back to plain classification. A broken
retrieval step must never take the triage pipeline down — a good-enough
answer is always better than a 500.
"""

from __future__ import annotations

import logging

from app.application.ports.classifier_port import ClassifierPort
from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis

logger = logging.getLogger(__name__)


class RagAssistedClassifier(ClassifierPort):
    """Fetch similar past tickets, hand them to the inner classifier."""

    def __init__(
        self,
        inner: ClassifierPort,
        similar_tickets: SimilarTicketsPort,
        top_k: int = 3,
    ) -> None:
        self._inner = inner
        self._similar_tickets = similar_tickets
        self._top_k = top_k

    def analyze(
        self,
        ticket: Ticket,
        similar_cases: list[SimilarCase] | None = None,
    ) -> TriageAnalysis:
        # Caller-supplied context takes precedence — it lets tests inject
        # deterministic fixtures and lets future callers (e.g. a tool-using
        # agent) bypass the retrieval step.
        resolved_cases = list(similar_cases) if similar_cases is not None else self._retrieve(ticket)

        analysis = self._inner.analyze(ticket, similar_cases=resolved_cases)

        # Inner classifiers may or may not attach the cases themselves.
        # Ensure the returned analysis always carries the context that
        # actually shaped the decision — callers (including the UI) rely
        # on this.
        if not analysis.similar_cases:
            analysis.similar_cases = resolved_cases
        return analysis

    def _retrieve(self, ticket: Ticket) -> list[SimilarCase]:
        query_text = f"{ticket.title} {ticket.description}".strip()
        if not query_text:
            return []
        try:
            return self._similar_tickets.find_similar(query_text, top_k=self._top_k)
        except Exception:
            # Pipeline-critical path — never propagate retrieval errors.
            logger.exception("similar-tickets retrieval failed, continuing without RAG context")
            return []
