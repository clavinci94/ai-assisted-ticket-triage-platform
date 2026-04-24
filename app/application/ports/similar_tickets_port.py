"""Port for retrieving historical tickets similar to an incoming one.

The triage pipeline uses this to enrich the LLM prompt with concrete past
routing decisions instead of relying on the model's prior alone. Keeping it
as an abstract port means the adapter (TF-IDF today, embeddings later) can
be swapped without touching business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.similar_case import SimilarCase


class SimilarTicketsPort(ABC):
    @abstractmethod
    def find_similar(self, text: str, top_k: int = 3) -> list[SimilarCase]:
        """Return up to ``top_k`` reviewed tickets most similar to ``text``.

        Implementations must return an empty list when no usable corpus
        exists yet (cold start). The caller treats that as "no retrieval
        context available" and degrades gracefully.
        """
        raise NotImplementedError

    @abstractmethod
    def rebuild(self) -> int:
        """Reindex from the current ticket corpus. Returns corpus size."""
        raise NotImplementedError
