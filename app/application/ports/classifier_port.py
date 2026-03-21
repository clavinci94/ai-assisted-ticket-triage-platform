from abc import ABC, abstractmethod

from app.application.dto.triage_result import TriageResult
from app.domain.entities.ticket import Ticket


class ClassifierPort(ABC):
    @abstractmethod
    def analyze(self, ticket: Ticket) -> TriageResult:
        raise NotImplementedError
