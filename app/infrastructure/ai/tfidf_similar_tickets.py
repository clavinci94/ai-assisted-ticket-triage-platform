"""TF-IDF-based retrieval adapter for the SimilarTicketsPort.

Trade-offs that drove this choice:

* **Zero new dependencies.** scikit-learn is already pinned for the baseline
  ML classifier. Using TF-IDF here keeps requirements.txt unchanged.
* **Corpus size is small.** Even a busy helpdesk produces O(10k) tickets per
  year. A sparse TF-IDF matrix + cosine NearestNeighbors answers in < 10 ms
  for that size, and fits in < 30 MB of RAM.
* **Swap later, not now.** When the corpus grows or multilingual recall
  becomes a bottleneck, switch the adapter to sentence-transformers +
  pgvector. The port contract does not change.

Only tickets with a confirmed ``final_department`` enter the corpus — the
whole point is to learn from *human-reviewed* routing, not from historical
AI guesses that may themselves have been wrong.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sqlalchemy.orm import Session

from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.domain.entities.similar_case import SimilarCase
from app.infrastructure.persistence.models import TicketRecordModel

logger = logging.getLogger(__name__)


@dataclass
class _Index:
    """Immutable snapshot of a fitted index. Swapped atomically on rebuild."""

    vectorizer: TfidfVectorizer
    neighbors: NearestNeighbors
    ticket_meta: list[SimilarCase]  # aligned with row order in the matrix


class TfidfSimilarTicketsAdapter(SimilarTicketsPort):
    """Retrieval adapter backed by TF-IDF + cosine NearestNeighbors.

    The adapter holds one lazily-built index. ``rebuild()`` constructs a
    new index and swaps it in under a lock; ``find_similar()`` reads the
    current index without locking (the reference assignment is atomic in
    CPython). This means concurrent requests during a rebuild still get a
    consistent — if slightly stale — answer.
    """

    MIN_CORPUS_SIZE = 3  # below this, retrieval is not meaningful

    # Empirically tuned on small corpora (< 200 tickets): below ~0.25 cosine,
    # TF-IDF on 1–2-grams produces matches that share a handful of incidental
    # tokens but are not topically related — they clutter the UI and erode
    # operator trust. Above this floor, a match means real lexical overlap.
    DEFAULT_MIN_SIMILARITY = 0.25

    def __init__(
        self,
        session_factory: Callable[[], Session],
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
    ) -> None:
        self._session_factory = session_factory
        self._min_similarity = min_similarity
        self._index: _Index | None = None
        self._rebuild_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Port API
    # ------------------------------------------------------------------

    def find_similar(self, text: str, top_k: int = 3) -> list[SimilarCase]:
        if not text or not text.strip():
            return []

        index = self._index
        if index is None or not index.ticket_meta:
            return []

        query_vector = index.vectorizer.transform([text])

        # ``n_neighbors`` may not exceed the corpus size.
        k = min(top_k, len(index.ticket_meta))
        distances, indices = index.neighbors.kneighbors(query_vector, n_neighbors=k)

        results: list[SimilarCase] = []
        for distance, row_idx in zip(distances[0], indices[0], strict=True):
            # sklearn's cosine distance is 1 - cosine_similarity. Convert back.
            similarity = max(0.0, 1.0 - float(distance))
            if similarity < self._min_similarity:
                continue
            base = index.ticket_meta[row_idx]
            results.append(
                SimilarCase(
                    ticket_id=base.ticket_id,
                    title=base.title,
                    final_department=base.final_department,
                    final_category=base.final_category,
                    final_team=base.final_team,
                    similarity_score=round(similarity, 4),
                )
            )
        return results

    def rebuild(self) -> int:
        """Rebuild the index from the current ticket corpus.

        Thread-safe. Returns the number of tickets that were indexed.
        A value below ``MIN_CORPUS_SIZE`` means retrieval is effectively
        disabled until more reviewed tickets exist.
        """

        with self._rebuild_lock:
            rows = self._load_reviewed_tickets()
            if len(rows) < self.MIN_CORPUS_SIZE:
                logger.info(
                    "tfidf rebuild skipped — only %d reviewed tickets (need %d)",
                    len(rows),
                    self.MIN_CORPUS_SIZE,
                )
                self._index = None
                return len(rows)

            texts = [self._row_to_text(row) for row in rows]
            vectorizer = TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
            )
            matrix = vectorizer.fit_transform(texts)

            neighbors = NearestNeighbors(metric="cosine", n_neighbors=min(5, len(rows)))
            neighbors.fit(matrix)

            meta = [self._row_to_meta(row) for row in rows]
            self._index = _Index(vectorizer=vectorizer, neighbors=neighbors, ticket_meta=meta)

            logger.info("tfidf rebuild complete — %d tickets indexed", len(rows))
            return len(rows)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_reviewed_tickets(self) -> list[TicketRecordModel]:
        """Return tickets that have a human-confirmed routing decision.

        The schema doesn't carry a dedicated ``final_department`` column —
        department is mutated in-place on the ticket. We therefore use
        ``reviewed_by IS NOT NULL`` as the signal that a human endorsed
        the current departmental routing.
        """
        session = self._session_factory()
        try:
            return session.query(TicketRecordModel).filter(TicketRecordModel.reviewed_by.isnot(None)).all()
        finally:
            session.close()

    @staticmethod
    def _row_to_text(row: TicketRecordModel) -> str:
        return f"{row.title or ''} {row.description or ''}".strip()

    @staticmethod
    def _row_to_meta(row: TicketRecordModel) -> SimilarCase:
        return SimilarCase(
            ticket_id=row.id,
            title=row.title or "",
            final_department=row.department or "",
            final_category=row.final_category or row.category or "unknown",
            final_team=row.final_team or row.team,
            similarity_score=0.0,  # populated per-query in find_similar
        )
