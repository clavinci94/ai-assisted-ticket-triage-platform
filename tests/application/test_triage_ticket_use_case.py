from app.application.use_cases.triage_ticket import TriageTicketUseCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.domain.enums.ticket_status import TicketStatus


class FakeClassifier:
    def analyze(self, ticket):
        return TriageAnalysis(
            predicted_category=TicketCategory.BUG,
            category_confidence=0.9,
            predicted_priority=TicketPriority.MEDIUM,
            priority_confidence=0.9,
            summary="summary",
            suggested_team="engineering-team",
            next_step="Investigate",
            rationale="test rationale",
            model_version="tfidf-mnb-v1",
            analyzed_at="2026-03-21T17:00:00Z",
        )


class FakeRepository:
    def __init__(self):
        self.created_ticket = None
        self.analysis_attached = None
        self.updated_status = None

    def create_ticket(self, ticket):
        self.created_ticket = ticket
        return ticket

    def attach_analysis(self, ticket_id, analysis):
        self.analysis_attached = (ticket_id, analysis)
        return None

    def update_status(self, ticket_id, status):
        self.updated_status = (ticket_id, status)
        return None


def test_triage_use_case_sets_triaged_status_and_preserves_audit_fields():
    ticket = Ticket(
        title="Checkout error",
        description="Users cannot pay",
        reporter="alice",
        source="internal",
    )
    repository = FakeRepository()
    classifier = FakeClassifier()

    use_case = TriageTicketUseCase(
        classifier=classifier,
        repository=repository,
    )

    result = use_case.execute(ticket)

    assert repository.created_ticket is ticket
    assert repository.analysis_attached is not None
    assert repository.updated_status == (ticket.id, TicketStatus.TRIAGED)

    assert result.analysis.model_version == "tfidf-mnb-v1"
    assert result.analysis.analyzed_at == "2026-03-21T17:00:00Z"
    assert result.final_category == TicketCategory.BUG
    assert result.final_team == "engineering-team"
