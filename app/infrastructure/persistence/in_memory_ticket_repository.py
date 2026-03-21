from app.application.dto.ticket_record import TicketRecord
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_status import TicketStatus


class InMemoryTicketRepository(TicketRepositoryPort):
    def __init__(self) -> None:
        self._records: dict[str, TicketRecord] = {}

    def create_ticket(self, ticket: Ticket) -> TicketRecord:
        record = TicketRecord(ticket=ticket)
        self._records[ticket.id] = record
        return record

    def attach_analysis(self, ticket_id: str, analysis: TriageAnalysis) -> TicketRecord:
        record = self._records[ticket_id]
        record.analysis = analysis
        return record

    def attach_decision(self, ticket_id: str, decision: TriageDecision) -> TicketRecord:
        record = self._records[ticket_id]
        record.decision = decision
        return record

    def update_status(self, ticket_id: str, status: TicketStatus) -> TicketRecord:
        record = self._records[ticket_id]
        record.ticket.status = status
        return record

    def get_ticket(self, ticket_id: str) -> TicketRecord | None:
        return self._records.get(ticket_id)

    def list_tickets(self) -> list[TicketRecord]:
        return list(self._records.values())
