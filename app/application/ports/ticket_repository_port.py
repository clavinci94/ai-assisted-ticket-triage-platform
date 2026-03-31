from abc import ABC, abstractmethod

from app.application.dto.ticket_record import TicketRecord
from app.domain.entities.assignment import Assignment
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_event import TicketEvent
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_status import TicketStatus


class TicketRepositoryPort(ABC):
    @abstractmethod
    def create_ticket(self, ticket: Ticket) -> TicketRecord:
        raise NotImplementedError

    @abstractmethod
    def attach_analysis(self, ticket_id: str, analysis: TriageAnalysis) -> TicketRecord:
        raise NotImplementedError

    @abstractmethod
    def update_department(self, ticket_id: str, department: str) -> TicketRecord:
        raise NotImplementedError

    @abstractmethod
    def attach_decision(self, ticket_id: str, decision: TriageDecision) -> TicketRecord:
        raise NotImplementedError

    @abstractmethod
    def attach_assignment(self, ticket_id: str, assignment: Assignment) -> TicketRecord:
        raise NotImplementedError

    @abstractmethod
    def update_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        actor: str | None = None,
        note: str | None = None,
    ) -> TicketRecord:
        raise NotImplementedError

    @abstractmethod
    def update_ticket_fields(
        self,
        ticket_id: str,
        *,
        priority: str | None = None,
        team: str | None = None,
        assignee: str | None = None,
        due_at=None,
        sla_breached: bool | None = None,
    ) -> TicketRecord:
        raise NotImplementedError

    @abstractmethod
    def add_event(
        self,
        ticket_id: str,
        event_type: str,
        actor: str | None,
        summary: str,
        details: str | None = None,
    ) -> TicketEvent:
        raise NotImplementedError

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> TicketRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_tickets(self) -> list[TicketRecord]:
        raise NotImplementedError
