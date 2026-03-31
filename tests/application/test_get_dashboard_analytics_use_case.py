from app.application.dto.ticket_record import TicketRecord
from app.application.use_cases.get_dashboard_analytics import (
    KNOWN_DEPARTMENTS,
    GetDashboardAnalyticsUseCase,
)
from app.domain.entities.ticket import Ticket
from app.domain.enums.ticket_status import TicketStatus


class FakeRepository:
    def __init__(self, records):
        self.records = records

    def list_tickets(self):
        return self.records


def make_record(title: str, department: str, status: TicketStatus) -> TicketRecord:
    return TicketRecord(
        ticket=Ticket(
            title=title,
            description=f"{title} description",
            reporter="claudio",
            source="internal",
            department=department,
            status=status,
        )
    )


def test_dashboard_analytics_includes_all_known_departments_even_without_tickets():
    repository = FakeRepository(
        [
            make_record("Login issue", "bank it support", TicketStatus.NEW),
            make_record("ATM sync problem", "Retail Banking", TicketStatus.TRIAGED),
        ]
    )

    result = GetDashboardAnalyticsUseCase(repository=repository).execute()

    distribution = result.department_distribution
    department_names = [item["name"] for item in distribution]
    department_counts = {item["name"]: item["value"] for item in distribution}

    assert department_names[: len(KNOWN_DEPARTMENTS)] == KNOWN_DEPARTMENTS
    assert department_counts["Bank-IT Support"] == 1
    assert department_counts["Retail Banking"] == 1
    assert department_counts["Corporate Banking"] == 0
    assert department_counts["Risk & Compliance"] == 0
    assert department_counts["Payments Operations"] == 0
    assert department_counts["Digital Channels"] == 0
    assert department_counts["Lending Services"] == 0
    assert "bank it support" not in department_counts
