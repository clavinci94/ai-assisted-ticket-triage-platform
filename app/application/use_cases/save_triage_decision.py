import logging

from app.application.dto.ticket_record import TicketRecord
from app.application.ports.similar_tickets_port import SimilarTicketsPort
from app.application.ports.ticket_repository_port import TicketRepositoryPort
from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_status import TicketStatus

logger = logging.getLogger(__name__)


class SaveTriageDecisionUseCase:
    """Persist a reviewer's decision and refresh the RAG index.

    The retrieval layer's whole pitch is that it learns from human-
    confirmed routing. A new reviewed ticket is therefore brand-new
    training data — we trigger an index rebuild as part of the same
    use case so the next triage call sees it. Rebuild is best-effort:
    a failed refresh logs and continues so the decision still saves.
    """

    def __init__(
        self,
        repository: TicketRepositoryPort,
        similar_tickets: SimilarTicketsPort | None = None,
    ) -> None:
        self.repository = repository
        self.similar_tickets = similar_tickets

    def execute(self, ticket_id: str, decision: TriageDecision) -> TicketRecord:
        self.repository.attach_decision(ticket_id, decision)
        updated_record = self.repository.update_status(
            ticket_id,
            TicketStatus.REVIEWED,
            actor=decision.reviewed_by,
        )

        if self.similar_tickets is not None:
            try:
                indexed = self.similar_tickets.rebuild()
                logger.info(
                    "RAG index refreshed after decision",
                    extra={"ticket_id": ticket_id, "corpus_size": indexed},
                )
            except Exception:
                logger.exception(
                    "RAG index refresh after decision failed",
                    extra={"ticket_id": ticket_id},
                )

        return updated_record
