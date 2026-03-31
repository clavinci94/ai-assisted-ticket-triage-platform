from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.application.dto.ticket_record import TicketRecord
from app.domain.constants.departments import KNOWN_DEPARTMENTS, canonicalize_department_label


@dataclass
class DashboardAnalyticsResult:
    stats: dict[str, int]
    status_distribution: list[dict[str, int | str]]
    category_distribution: list[dict[str, int | str]]
    priority_distribution: list[dict[str, int | str]]
    department_distribution: list[dict[str, int | str]]
    management_metrics: dict[str, int]
    review_funnel: list[dict[str, int | str]]
    ai_acceptance: list[dict[str, int | str]]
    needs_attention: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]


class GetDashboardAnalyticsUseCase:
    def __init__(self, repository) -> None:
        self.repository = repository

    def execute(self) -> DashboardAnalyticsResult:
        records = self.repository.list_tickets()
        tickets = [self._record_to_dict(record) for record in records]

        total = len(tickets)
        triaged = sum(1 for ticket in tickets if ticket["status"] == "triaged")
        reviewed = sum(1 for ticket in tickets if ticket["status"] == "reviewed")
        assigned = sum(1 for ticket in tickets if ticket["status"] == "assigned")
        reviewed_or_beyond = sum(
          1 for ticket in tickets if ticket["status"] in {"reviewed", "assigned"}
        )

        reviewed_tickets = [ticket for ticket in tickets if ticket["reviewed"]]
        accepted_ai_count = sum(
            1 for ticket in reviewed_tickets if ticket["accepted_ai_suggestion"] is True
        )
        adjusted_ai_count = max(len(reviewed_tickets) - accepted_ai_count, 0)

        acceptance_rate = round((accepted_ai_count / len(reviewed_tickets)) * 100) if reviewed_tickets else 0
        assignment_rate = round((assigned / total) * 100) if total else 0
        review_coverage = round((reviewed_or_beyond / total) * 100) if total else 0

        needs_attention = sorted(
            [
                ticket
                for ticket in tickets
                if ticket["priority"] in {"high", "critical"} or ticket["status"] == "triaged"
            ],
            key=lambda item: {
                "critical": 4,
                "high": 3,
                "medium": 2,
                "low": 1,
                "unknown": 0,
            }.get(item["priority"], 0),
            reverse=True,
        )[:5]

        recent_activity = list(reversed(tickets))[:5]

        return DashboardAnalyticsResult(
            stats={
                "total": total,
                "triaged": triaged,
                "reviewed": reviewed,
                "assigned": assigned,
            },
            status_distribution=self._distribution(
                tickets,
                "status",
                ["new", "triaged", "reviewed", "assigned"],
            ),
            category_distribution=self._distribution(
                tickets,
                "category",
                ["bug", "feature", "support", "requirement", "question"],
            ),
            priority_distribution=self._distribution(
                tickets,
                "priority",
                ["low", "medium", "high", "critical"],
            ),
            department_distribution=self._distribution(
                tickets,
                "department",
                KNOWN_DEPARTMENTS,
                include_empty_labels=True,
            ),
            management_metrics={
                "reviewed_count": len(reviewed_tickets),
                "accepted_ai_count": accepted_ai_count,
                "acceptance_rate": acceptance_rate,
                "assignment_rate": assignment_rate,
                "review_coverage": review_coverage,
            },
            review_funnel=[
                {"name": "created", "value": total},
                {"name": "triaged", "value": triaged},
                {"name": "reviewed", "value": reviewed_or_beyond},
                {"name": "assigned", "value": assigned},
            ],
            ai_acceptance=[
                {"name": "accepted", "value": accepted_ai_count},
                {"name": "adjusted", "value": adjusted_ai_count},
            ],
            needs_attention=needs_attention,
            recent_activity=recent_activity,
        )

    def _record_to_dict(self, record: TicketRecord) -> dict[str, Any]:
        ticket = record.ticket
        analysis = record.analysis
        decision = record.decision
        assignment = record.assignment

        category = (
            decision.final_category.value
            if decision and getattr(decision, "final_category", None)
            else (
                analysis.predicted_category.value
                if analysis and getattr(analysis, "predicted_category", None)
                else "unknown"
            )
        )

        priority = (
            decision.final_priority.value
            if decision and getattr(decision, "final_priority", None)
            else (
                analysis.predicted_priority.value
                if analysis and getattr(analysis, "predicted_priority", None)
                else "unknown"
            )
        )

        return {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "reporter": ticket.reporter,
            "status": ticket.status.value,
            "category": category,
            "priority": priority,
            "department": canonicalize_department_label(ticket.department),
            "accepted_ai_suggestion": bool(getattr(decision, "accepted_ai_suggestion", False)) if decision else False,
            "reviewed": decision is not None,
            "assigned": assignment is not None,
        }

    def _distribution(
        self,
        items: list[dict[str, Any]],
        key: str,
        ordered_labels: list[str],
        include_empty_labels: bool = False,
    ) -> list[dict[str, int | str]]:
        counts = Counter((item.get(key) or "unknown").lower() for item in items)
        result: list[dict[str, int | str]] = []

        for label in ordered_labels:
            normalized_label = label.lower()
            value = counts.pop(normalized_label, 0)
            if value or include_empty_labels:
                result.append({"name": label, "value": value})

        for name, value in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            result.append({"name": name, "value": value})

        return result
