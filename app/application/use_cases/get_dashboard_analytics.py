import contextlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    team_distribution: list[dict[str, int | str]]
    management_metrics: dict[str, int]
    sla_metrics: dict[str, int]
    review_funnel: list[dict[str, int | str]]
    ai_acceptance: list[dict[str, int | str]]
    processing_time_by_priority: list[dict[str, int | str]]
    top_assignees: list[dict[str, int | str]]
    ticket_volume_over_time: list[dict[str, int | str]]
    backlog_development: list[dict[str, int | str]]
    needs_attention: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]
    impact_distribution: list[dict[str, int | str]]
    urgency_distribution: list[dict[str, int | str]]
    solvability_distribution: list[dict[str, int | str]]
    effort_buckets: list[dict[str, int | str]]
    composite_priority_buckets: list[dict[str, int | str]]
    ke_metrics: dict[str, int]


class GetDashboardAnalyticsUseCase:
    def __init__(self, repository) -> None:
        self.repository = repository

    def execute(self) -> DashboardAnalyticsResult:
        records = self.repository.list_tickets()
        tickets = [self._record_to_dict(record) for record in records]
        now = datetime.now(UTC)

        total = len(tickets)
        triaged = sum(1 for ticket in tickets if ticket["status"] == "triaged")
        reviewed = sum(1 for ticket in tickets if ticket["status"] == "reviewed")
        assigned = sum(1 for ticket in tickets if ticket["status"] == "assigned")
        closed = sum(1 for ticket in tickets if ticket["status"] == "closed")
        reviewed_or_beyond = sum(
            1 for ticket in tickets if ticket["status"] in {"reviewed", "assigned", "closed"}
        )

        reviewed_tickets = [ticket for ticket in tickets if ticket["reviewed"]]
        accepted_ai_count = sum(1 for ticket in reviewed_tickets if ticket["accepted_ai_suggestion"] is True)
        adjusted_ai_count = max(len(reviewed_tickets) - accepted_ai_count, 0)

        acceptance_rate = round((accepted_ai_count / len(reviewed_tickets)) * 100) if reviewed_tickets else 0
        assignment_rate = round((assigned / total) * 100) if total else 0
        review_coverage = round((reviewed_or_beyond / total) * 100) if total else 0

        needs_attention = sorted(
            [
                ticket
                for ticket in tickets
                if ticket["priority"] in {"high", "critical"}
                or ticket["status"] == "triaged"
                or ticket["sla_breached"] is True
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

        recent_activity = sorted(
            tickets,
            key=lambda ticket: (
                self._coerce_datetime(ticket["updated_at"]) or datetime.min.replace(tzinfo=UTC)
            ),
            reverse=True,
        )[:5]

        return DashboardAnalyticsResult(
            stats={
                "total": total,
                "triaged": triaged,
                "reviewed": reviewed,
                "assigned": assigned,
                "closed": closed,
            },
            status_distribution=self._distribution(
                tickets,
                "status",
                ["new", "triaged", "reviewed", "assigned", "closed"],
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
            team_distribution=self._distribution(
                tickets,
                "team",
                [],
            ),
            management_metrics={
                "reviewed_count": len(reviewed_tickets),
                "accepted_ai_count": accepted_ai_count,
                "acceptance_rate": acceptance_rate,
                "assignment_rate": assignment_rate,
                "review_coverage": review_coverage,
            },
            sla_metrics=self._build_sla_metrics(tickets, now),
            review_funnel=[
                {"name": "created", "value": total},
                {"name": "triaged", "value": triaged},
                {"name": "reviewed", "value": reviewed_or_beyond},
                {"name": "assigned", "value": assigned},
                {"name": "closed", "value": closed},
            ],
            ai_acceptance=[
                {"name": "accepted", "value": accepted_ai_count},
                {"name": "adjusted", "value": adjusted_ai_count},
            ],
            processing_time_by_priority=self._build_processing_time_by_priority(tickets),
            top_assignees=self._build_top_assignees(tickets),
            ticket_volume_over_time=self._build_ticket_volume_over_time(tickets),
            backlog_development=self._build_backlog_development(tickets),
            needs_attention=needs_attention,
            recent_activity=recent_activity,
            impact_distribution=self._build_score_distribution(tickets, "impact_score"),
            urgency_distribution=self._build_score_distribution(tickets, "urgency_score"),
            solvability_distribution=self._build_solvability_distribution(tickets),
            effort_buckets=self._build_effort_buckets(tickets),
            composite_priority_buckets=self._build_composite_priority_buckets(tickets),
            ke_metrics=self._build_ke_metrics(tickets),
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
                ticket.category
                if ticket.category
                else (
                    analysis.predicted_category.value
                    if analysis and getattr(analysis, "predicted_category", None)
                    else "unknown"
                )
            )
        )

        priority = (
            decision.final_priority.value
            if decision and getattr(decision, "final_priority", None)
            else (
                ticket.priority
                if ticket.priority
                else (
                    analysis.predicted_priority.value
                    if analysis and getattr(analysis, "predicted_priority", None)
                    else "unknown"
                )
            )
        )

        created_at = self._record_created_at(record)
        updated_at = self._record_updated_at(record)
        closed_at = self._record_closed_at(record)
        assignee = (
            ticket.assignee
            or getattr(assignment, "assignee", None)
            or getattr(assignment, "assigned_by", None)
            or getattr(decision, "reviewed_by", None)
        )
        team = (
            getattr(assignment, "assigned_team", None)
            or getattr(decision, "final_team", None)
            or ticket.team
            or (analysis.suggested_team if analysis else None)
        )

        prioritization = getattr(record, "prioritization", None)

        return {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "reporter": ticket.reporter,
            "status": ticket.status.value,
            "category": category,
            "priority": priority,
            "department": canonicalize_department_label(ticket.department),
            "team": team or "Nicht zugewiesen",
            "assignee": assignee,
            "due_at": ticket.due_at,
            "sla_breached": bool(ticket.sla_breached),
            "created_at": created_at,
            "updated_at": updated_at,
            "closed_at": closed_at,
            "accepted_ai_suggestion": bool(getattr(decision, "accepted_ai_suggestion", False))
            if decision
            else False,
            "reviewed": decision is not None,
            "assigned": assignment is not None,
            "impact_score": getattr(prioritization, "impact_score", None),
            "urgency_score": getattr(prioritization, "urgency_score", None),
            "effort_estimate_minutes": getattr(prioritization, "effort_estimate_minutes", None),
            "solvability": (prioritization.solvability.value if prioritization else None),
            "composite_priority": getattr(prioritization, "composite_priority", None),
            "auto_resolve_eligible": getattr(prioritization, "auto_resolve_eligible", None),
        }

    def _record_created_at(self, record: TicketRecord):
        timestamps = [event.created_at for event in record.events if event.created_at]
        if timestamps:
            return min(timestamps)
        if record.analysis and getattr(record.analysis, "analyzed_at", None):
            return self._coerce_datetime(record.analysis.analyzed_at)
        return None

    def _record_updated_at(self, record: TicketRecord):
        timestamps = [event.created_at for event in record.events if event.created_at]
        if timestamps:
            return max(timestamps)
        if record.analysis and getattr(record.analysis, "analyzed_at", None):
            return self._coerce_datetime(record.analysis.analyzed_at)
        return None

    def _record_closed_at(self, record: TicketRecord):
        if record.ticket.status.value != "closed":
            return None

        closed_events = [
            event.created_at
            for event in record.events
            if event.created_at
            and event.event_type == "status_changed"
            and "Geschlossen" in (event.details or "")
        ]
        if closed_events:
            return max(closed_events)

        return self._record_updated_at(record)

    def _build_sla_metrics(self, tickets: list[dict[str, Any]], now: datetime) -> dict[str, int]:
        metrics = {
            "total_with_sla": 0,
            "in_sla": 0,
            "due_soon": 0,
            "overdue": 0,
            "breached": 0,
        }

        for ticket in tickets:
            due_at = self._coerce_datetime(ticket.get("due_at"))
            breached = bool(ticket.get("sla_breached"))
            is_closed = ticket.get("status") == "closed"

            if not due_at and not breached:
                continue

            metrics["total_with_sla"] += 1

            if breached:
                metrics["breached"] += 1
                continue

            if due_at is None:
                continue

            if not is_closed and due_at < now:
                metrics["overdue"] += 1
            elif not is_closed and due_at <= now + timedelta(hours=24):
                metrics["due_soon"] += 1
            else:
                metrics["in_sla"] += 1

        return metrics

    def _build_processing_time_by_priority(self, tickets: list[dict[str, Any]]) -> list[dict[str, int | str]]:
        grouped_durations: dict[str, list[float]] = defaultdict(list)

        for ticket in tickets:
            created_at = self._coerce_datetime(ticket.get("created_at"))
            finished_at = self._coerce_datetime(ticket.get("closed_at")) or self._coerce_datetime(
                ticket.get("updated_at")
            )
            priority = str(ticket.get("priority") or "unknown").lower()

            if created_at is None or finished_at is None or finished_at < created_at:
                continue

            grouped_durations[priority].append((finished_at - created_at).total_seconds() / 3600)

        ordered_priorities = ["low", "medium", "high", "critical"]
        items: list[dict[str, int | str]] = []

        for priority in ordered_priorities:
            durations = grouped_durations.pop(priority, [])
            if not durations:
                continue
            items.append(
                {
                    "priority": priority,
                    "average_hours": round(sum(durations) / len(durations)),
                    "ticket_count": len(durations),
                }
            )

        for priority, durations in sorted(grouped_durations.items()):
            items.append(
                {
                    "priority": priority,
                    "average_hours": round(sum(durations) / len(durations)),
                    "ticket_count": len(durations),
                }
            )

        return items

    def _build_top_assignees(self, tickets: list[dict[str, Any]]) -> list[dict[str, int | str]]:
        grouped: dict[str, dict[str, int]] = defaultdict(
            lambda: {"active_count": 0, "closed_count": 0, "total_count": 0}
        )

        for ticket in tickets:
            assignee = ticket.get("assignee")
            if not assignee:
                continue

            grouped[assignee]["total_count"] += 1
            if ticket.get("status") == "closed":
                grouped[assignee]["closed_count"] += 1
            else:
                grouped[assignee]["active_count"] += 1

        return [
            {
                "name": name,
                "active_count": stats["active_count"],
                "closed_count": stats["closed_count"],
                "total_count": stats["total_count"],
            }
            for name, stats in sorted(
                grouped.items(),
                key=lambda item: (
                    -item[1]["closed_count"],
                    -item[1]["total_count"],
                    item[0].lower(),
                ),
            )[:10]
        ]

    def _build_ticket_volume_over_time(self, tickets: list[dict[str, Any]]) -> list[dict[str, int | str]]:
        counts: Counter[str] = Counter()

        for ticket in tickets:
            created_at = self._coerce_datetime(ticket.get("created_at"))
            if created_at is None:
                continue
            counts[created_at.date().isoformat()] += 1

        return [{"date": date_key, "value": value} for date_key, value in sorted(counts.items())]

    def _build_backlog_development(self, tickets: list[dict[str, Any]]) -> list[dict[str, int | str]]:
        created_counts: Counter[str] = Counter()
        closed_counts: Counter[str] = Counter()

        for ticket in tickets:
            created_at = self._coerce_datetime(ticket.get("created_at"))
            closed_at = self._coerce_datetime(ticket.get("closed_at"))

            if created_at is not None:
                created_counts[created_at.date().isoformat()] += 1
            if closed_at is not None:
                closed_counts[closed_at.date().isoformat()] += 1

        all_dates = sorted(set(created_counts) | set(closed_counts))
        backlog = 0
        points: list[dict[str, int | str]] = []

        for date_key in all_dates:
            created_value = created_counts.get(date_key, 0)
            closed_value = closed_counts.get(date_key, 0)
            backlog += created_value - closed_value
            points.append(
                {
                    "date": date_key,
                    "created": created_value,
                    "closed": closed_value,
                    "backlog": max(backlog, 0),
                }
            )

        return points

    def _build_score_distribution(
        self, tickets: list[dict[str, Any]], key: str
    ) -> list[dict[str, int | str]]:
        """Counts per integer score 1–5. Tickets without a value are skipped."""

        counts: Counter[int] = Counter()
        for ticket in tickets:
            value = ticket.get(key)
            if value is None:
                continue
            try:
                score = int(value)
            except (TypeError, ValueError):
                continue
            if 1 <= score <= 5:
                counts[score] += 1
        return [{"name": str(score), "value": counts.get(score, 0)} for score in range(1, 6)]

    def _build_solvability_distribution(self, tickets: list[dict[str, Any]]) -> list[dict[str, int | str]]:
        labels = {
            "self-service": "Self-Service",
            "l1": "L1",
            "l2": "L2",
            "specialist": "Spezialist",
        }
        counts: Counter[str] = Counter()
        for ticket in tickets:
            raw = ticket.get("solvability")
            if not raw:
                continue
            counts[str(raw).lower()] += 1
        return [{"name": label, "value": counts.get(key, 0)} for key, label in labels.items()]

    def _build_effort_buckets(self, tickets: list[dict[str, Any]]) -> list[dict[str, int | str]]:
        buckets = [
            ("< 15 min", 0, 15),
            ("15–60 min", 15, 60),
            ("1–2 h", 60, 120),
            ("2–4 h", 120, 240),
            ("> 4 h", 240, 10**9),
        ]
        counts: dict[str, int] = {label: 0 for label, _, _ in buckets}
        for ticket in tickets:
            value = ticket.get("effort_estimate_minutes")
            if value is None:
                continue
            try:
                minutes = int(value)
            except (TypeError, ValueError):
                continue
            for label, lower, upper in buckets:
                if lower <= minutes < upper:
                    counts[label] += 1
                    break
        return [{"name": label, "value": counts[label]} for label, _, _ in buckets]

    def _build_composite_priority_buckets(self, tickets: list[dict[str, Any]]) -> list[dict[str, int | str]]:
        buckets = [
            ("Niedrig (1–5)", 1, 6),
            ("Mittel (6–11)", 6, 12),
            ("Hoch (12–19)", 12, 20),
            ("Kritisch (20–25)", 20, 26),
        ]
        counts: dict[str, int] = {label: 0 for label, _, _ in buckets}
        for ticket in tickets:
            value = ticket.get("composite_priority")
            if value is None:
                continue
            try:
                score = float(value)
            except (TypeError, ValueError):
                continue
            for label, lower, upper in buckets:
                if lower <= score < upper:
                    counts[label] += 1
                    break
        return [{"name": label, "value": counts[label]} for label, _, _ in buckets]

    def _build_ke_metrics(self, tickets: list[dict[str, Any]]) -> dict[str, int]:
        efforts: list[int] = []
        prioritized = 0
        auto_resolve = 0
        self_service = 0
        for ticket in tickets:
            if ticket.get("impact_score") is not None:
                prioritized += 1
            if ticket.get("auto_resolve_eligible"):
                auto_resolve += 1
            if str(ticket.get("solvability") or "").lower() == "self-service":
                self_service += 1
            effort = ticket.get("effort_estimate_minutes")
            if effort is not None:
                with contextlib.suppress(TypeError, ValueError):
                    efforts.append(int(effort))
        avg_effort = round(sum(efforts) / len(efforts)) if efforts else 0
        return {
            "prioritized_count": prioritized,
            "auto_resolve_count": auto_resolve,
            "self_service_count": self_service,
            "avg_effort_minutes": avg_effort,
            "total_effort_hours": round(sum(efforts) / 60) if efforts else 0,
        }

    def _distribution(
        self,
        items: list[dict[str, Any]],
        key: str,
        ordered_labels: list[str],
        include_empty_labels: bool = False,
    ) -> list[dict[str, int | str]]:
        normalized_items = [str(item.get(key) or "unknown") for item in items]
        counts = Counter(value.lower() for value in normalized_items)
        display_labels = {value.lower(): value for value in normalized_items if value}
        result: list[dict[str, int | str]] = []

        for label in ordered_labels:
            normalized_label = label.lower()
            value = counts.pop(normalized_label, 0)
            if value or include_empty_labels:
                result.append({"name": label, "value": value})

        for name, value in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            result.append({"name": display_labels.get(name, name), "value": value})

        return result

    def _coerce_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                return None
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        return None
