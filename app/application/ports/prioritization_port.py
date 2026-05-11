from abc import ABC, abstractmethod

from app.domain.entities.prioritization import Prioritization
from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis


class PrioritizationPort(ABC):
    @abstractmethod
    def prioritize(
        self,
        ticket: Ticket,
        analysis: TriageAnalysis,
        similar_cases: list[SimilarCase] | None = None,
    ) -> Prioritization:
        """Score ``ticket`` along the four KE dimensions and derive signals.

        The analysis is passed in so the prioritiser can react to the
        classifier's category/priority/team output (e.g. "AML category →
        impact = 5"). ``similar_cases`` is the same retrieval context the
        classifier saw and is used to estimate effort by averaging the
        resolution time of human-reviewed neighbours.
        """
        raise NotImplementedError
