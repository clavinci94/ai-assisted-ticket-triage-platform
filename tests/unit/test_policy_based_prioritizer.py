"""Tests for the YAML-driven Knowledge-Engineering prioritizer."""

from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.solvability_level import SolvabilityLevel
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.domain.enums.ticket_status import TicketStatus
from app.infrastructure.ai.policy_based_prioritizer import PolicyBasedPrioritizer


def _ticket(**overrides) -> Ticket:
    defaults: dict = {
        "id": "T-1",
        "title": "Sample",
        "description": "Sample description",
        "reporter": "alice",
        "source": "internal",
        "department": "Bank-IT Support",
        "category": None,
        "priority": None,
        "team": None,
        "assignee": None,
        "due_at": None,
        "tags": [],
        "sla_breached": False,
        "status": TicketStatus.NEW,
        "department_locked": False,
    }
    defaults.update(overrides)
    return Ticket(**defaults)


def _analysis(
    *,
    category: TicketCategory = TicketCategory.SUPPORT,
    priority: TicketPriority = TicketPriority.MEDIUM,
    confidence: float = 0.9,
) -> TriageAnalysis:
    return TriageAnalysis(
        predicted_category=category,
        category_confidence=confidence,
        predicted_priority=priority,
        priority_confidence=confidence,
        summary="",
        suggested_team="",
        suggested_department="",
        next_step="",
        rationale="",
        model_version="test",
        similar_cases=[],
    )


def test_aml_tag_yields_max_priority_and_specialist():
    p = PolicyBasedPrioritizer()
    result = p.prioritize(
        _ticket(tags=["aml"], department="Risk & Compliance"),
        _analysis(),
    )
    assert result.impact_score == 5
    assert result.urgency_score == 5
    assert result.composite_priority == 25.0
    assert result.solvability == SolvabilityLevel.SPECIALIST


def test_password_self_service_attaches_runbook():
    p = PolicyBasedPrioritizer()
    result = p.prioritize(
        _ticket(title="Passwort vergessen", tags=["password"]),
        _analysis(confidence=0.9),
    )
    assert result.solvability == SolvabilityLevel.SELF_SERVICE
    assert result.runbook_url is not None
    # confidence > threshold => auto-resolve
    assert result.auto_resolve_eligible is True


def test_self_service_below_confidence_is_not_auto_resolve():
    p = PolicyBasedPrioritizer()
    result = p.prioritize(
        _ticket(title="Passwort vergessen", tags=["password"]),
        _analysis(confidence=0.2),
    )
    assert result.solvability == SolvabilityLevel.SELF_SERVICE
    assert result.auto_resolve_eligible is False


def test_effort_estimate_averages_similar_neighbours():
    p = PolicyBasedPrioritizer()
    cases = [
        SimilarCase(
            ticket_id=f"HIST-{i}",
            title=f"neighbour {i}",
            final_department="Bank-IT Support",
            final_category="support",
            final_team="team",
            similarity_score=0.5,
            effort_estimate_minutes=minutes,
        )
        for i, minutes in enumerate([30, 60, 90], start=1)
    ]
    result = p.prioritize(_ticket(), _analysis(), similar_cases=cases)
    assert result.effort_estimate_minutes == 60  # mean of 30/60/90


def test_no_neighbours_falls_back_to_yaml_default_effort():
    p = PolicyBasedPrioritizer()
    result = p.prioritize(_ticket(), _analysis(), similar_cases=[])
    assert result.effort_estimate_minutes == 60  # default_effort_minutes in YAML


def test_default_rule_kicks_in_when_no_match():
    p = PolicyBasedPrioritizer()
    result = p.prioritize(_ticket(department="Unbekannte Abteilung"), _analysis())
    # Default block in YAML: impact=2, urgency=2, solvability=l2 → 4
    # (kept low so the Mittel-bucket isn't a catch-all for unmatched tickets)
    assert result.impact_score == 2
    assert result.urgency_score == 2
    assert result.composite_priority == 4.0
    assert result.solvability == SolvabilityLevel.L2


def test_tag_alone_matches_when_title_also_listed():
    """Regression: tags_any + title_any are OR'd, so a tag hit alone is enough."""
    p = PolicyBasedPrioritizer()
    # Use AML tag with a title that doesn't contain AML keywords.
    result = p.prioritize(
        _ticket(tags=["aml"], title="Nichts Bemerkenswertes", description=""),
        _analysis(),
    )
    assert result.impact_score == 5
    assert result.solvability == SolvabilityLevel.SPECIALIST


def test_title_alone_matches_when_tags_empty():
    """Regression: a tag-less ticket hits a tag+title rule via the title keyword."""
    p = PolicyBasedPrioritizer()
    result = p.prioritize(
        _ticket(tags=[], title="VPN-Zugang funktioniert nicht", description="Citrix bricht ab."),
        _analysis(),
    )
    # vpn-blocking rule: impact=3, urgency=4
    assert result.impact_score == 3
    assert result.urgency_score == 4
    assert result.solvability == SolvabilityLevel.L1
    assert result.runbook_url is not None
