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
            suggested_department="Payments Operations",
            next_step="Investigate",
            rationale="test rationale",
            model_version="tfidf-mnb-v1",
            analyzed_at="2026-03-21T17:00:00Z",
        )


class FakeRepository:
    def __init__(self):
        self.created_ticket = None
        self.analysis_attached = None
        self.updated_department = None
        self.updated_status = None

    def create_ticket(self, ticket):
        self.created_ticket = ticket
        return ticket

    def attach_analysis(self, ticket_id, analysis):
        self.analysis_attached = (ticket_id, analysis)
        return None

    def update_department(self, ticket_id, department):
        self.updated_department = (ticket_id, department)
        return None

    def update_status(self, ticket_id, status, actor=None, note=None):
        self.updated_status = (ticket_id, status, actor, note)
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
    assert repository.updated_department == (ticket.id, "Payments Operations")
    assert repository.updated_status == (ticket.id, TicketStatus.TRIAGED, "ai-system", None)

    assert result.analysis.model_version == "tfidf-mnb-v1"
    assert result.analysis.analyzed_at == "2026-03-21T17:00:00Z"
    assert result.final_category == TicketCategory.BUG
    assert result.final_team == "engineering-team"
    assert ticket.department == "Payments Operations"
    assert ticket.category == "bug"
    assert ticket.priority == "medium"
    assert ticket.team == "engineering-team"


def test_triage_use_case_keeps_manual_department_when_locked():
    ticket = Ticket(
        title="SEPA-Buchung doppelt",
        description="Zahlungen werden doppelt verbucht.",
        reporter="alice",
        source="internal",
        department="Risk & Compliance",
        department_locked=True,
    )
    repository = FakeRepository()
    classifier = FakeClassifier()

    use_case = TriageTicketUseCase(
        classifier=classifier,
        repository=repository,
    )

    result = use_case.execute(ticket)

    assert result.analysis.suggested_department == "Payments Operations"
    assert repository.updated_department == (ticket.id, "Risk & Compliance")
    assert ticket.department == "Risk & Compliance"


def test_triage_use_case_preserves_existing_ticket_metadata():
    ticket = Ticket(
        title="Mobile Banking Störung",
        description="Anmeldung schlägt fehl und benötigt rasche Bearbeitung.",
        reporter="alice",
        source="internal",
        category="support",
        priority="high",
        team="Digital Operations",
        assignee="claudio",
        tags=["Mobile App", "VIP"],
        sla_breached=True,
    )
    repository = FakeRepository()
    classifier = FakeClassifier()

    use_case = TriageTicketUseCase(
        classifier=classifier,
        repository=repository,
    )

    use_case.execute(ticket)

    assert ticket.category == "support"
    assert ticket.priority == "high"
    assert ticket.team == "Digital Operations"
    assert ticket.assignee == "claudio"
    assert ticket.tags == ["Mobile App", "VIP"]
    assert ticket.sla_breached is True
