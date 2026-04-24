"""Reference to a historical ticket that resembles an incoming one.

A SimilarCase is emitted by the retrieval layer and travels through the
triage pipeline as read-only context for the LLM and as audit breadcrumbs
for the operator UI. It is deliberately shallow — just enough to (a) let
the model recognize a routing pattern and (b) let a human click through to
the original ticket in the dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimilarCase:
    ticket_id: str
    title: str
    final_department: str
    final_category: str
    final_team: str | None
    similarity_score: float  # cosine similarity, 0.0–1.0
