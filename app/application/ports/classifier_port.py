from abc import ABC, abstractmethod

from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis


class ClassifierPort(ABC):
    @abstractmethod
    def analyze(
        self,
        ticket: Ticket,
        similar_cases: list[SimilarCase] | None = None,
    ) -> TriageAnalysis:
        """Produce a triage analysis for ``ticket``.

        ``similar_cases`` is optional retrieval context: past tickets that
        look like this one, together with the human-confirmed routing each
        ended up with. Implementations may use it to improve the output
        (e.g. as few-shot examples in a prompt) or ignore it entirely.
        Callers must treat ``similar_cases=None`` and ``similar_cases=[]``
        as equivalent — "no context available".
        """
        raise NotImplementedError
