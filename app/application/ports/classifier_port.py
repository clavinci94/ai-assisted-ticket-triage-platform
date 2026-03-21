from abc import ABC, abstractmethod

from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis


class ClassifierPort(ABC):
    @abstractmethod
    def analyze(self, ticket: Ticket) -> TriageAnalysis:
        raise NotImplementedError
