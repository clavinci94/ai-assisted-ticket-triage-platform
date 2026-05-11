from dataclasses import dataclass, field

from app.domain.enums.solvability_level import SolvabilityLevel


@dataclass
class Prioritization:
    """Knowledge-engineered prioritisation alongside the AI classification.

    The four input dimensions answer four operational questions:

    * ``impact_score``    — how important is this? (1 minor / 5 critical)
    * ``urgency_score``   — how quickly must we act? (1 / 5)
    * ``effort_estimate_minutes`` — how expensive will this be? (RAG average)
    * ``solvability``     — can it be auto-resolved or does L2 / specialist need to look?

    The two derived signals drive UI behaviour:

    * ``composite_priority`` = impact × urgency, used for backlog sort
    * ``auto_resolve_eligible`` = self-service ∧ confidence-high, used to
      surface a runbook to the user before a human picks it up
    """

    impact_score: int
    urgency_score: int
    effort_estimate_minutes: int
    solvability: SolvabilityLevel
    composite_priority: float
    auto_resolve_eligible: bool
    runbook_url: str | None = None
    rationale: str = ""
    matched_rules: list[str] = field(default_factory=list)
