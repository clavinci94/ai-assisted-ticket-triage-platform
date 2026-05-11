"""YAML-rule-based prioritisation adapter.

Reads a knowledge-engineering policy (impact, urgency, solvability,
runbook URLs) from ``app/infrastructure/triage_policy.yaml`` and combines
it with retrieval-based effort estimation: the expected effort is the
mean ``effort_estimate_minutes`` of the top-k similar reviewed tickets,
with a YAML-configured fallback if no neighbours are available.

The composite priority is intentionally simple — ``impact × urgency`` —
so it stays explainable to operators. ``auto_resolve_eligible`` is true
when a rule labels the ticket as ``self-service`` AND the classifier's
category_confidence clears the configured threshold; in that case the UI
should surface ``runbook_url`` to the reporter before a human picks the
ticket up.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from app.application.ports.prioritization_port import PrioritizationPort
from app.domain.entities.prioritization import Prioritization
from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.solvability_level import SolvabilityLevel

_LOGGER = logging.getLogger(__name__)

_DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / "triage_policy.yaml"


class PolicyBasedPrioritizer(PrioritizationPort):
    """Rule-based prioritiser that reads its knowledge from a YAML file."""

    def __init__(self, policy_path: Path | str | None = None) -> None:
        self._policy_path = Path(policy_path) if policy_path else _DEFAULT_POLICY_PATH
        self._policy = self._load_policy(self._policy_path)

    # ------------------------------------------------------------------
    # PrioritizationPort
    # ------------------------------------------------------------------

    def prioritize(
        self,
        ticket: Ticket,
        analysis: TriageAnalysis,
        similar_cases: list[SimilarCase] | None = None,
    ) -> Prioritization:
        context = self._build_context(ticket, analysis)

        impact = None
        urgency = None
        solvability: str | None = None
        rationale_parts: list[str] = []
        matched_rule_ids: list[str] = []
        runbook_url: str | None = None

        for rule in self._policy.get("rules", []):
            if not self._rule_matches(rule.get("match", {}), context):
                continue
            settings = rule.get("set", {})
            if "impact_score" in settings:
                impact = settings["impact_score"]
            if "urgency_score" in settings:
                urgency = settings["urgency_score"]
            if "solvability" in settings:
                solvability = settings["solvability"]
            if "runbook_url" in settings and runbook_url is None:
                runbook_url = settings["runbook_url"]
            if "rationale" in settings:
                rationale_parts.append(str(settings["rationale"]))
            matched_rule_ids.append(rule.get("id", "<unnamed>"))

        defaults = self._policy.get("default", {})
        if impact is None:
            impact = defaults.get("impact_score", 3)
        if urgency is None:
            urgency = defaults.get("urgency_score", 3)
        if solvability is None:
            solvability = defaults.get("solvability", "l2")
        if not rationale_parts and "rationale" in defaults:
            rationale_parts.append(str(defaults["rationale"]))

        impact = self._clamp_score(impact)
        urgency = self._clamp_score(urgency)
        solvability_level = self._parse_solvability(solvability)
        effort_minutes = self._estimate_effort(similar_cases)

        composite_priority = float(impact * urgency)
        threshold = float(self._policy.get("self_service_confidence_threshold", 0.6))
        auto_resolve = (
            solvability_level == SolvabilityLevel.SELF_SERVICE
            and getattr(analysis, "category_confidence", 0.0) >= threshold
            and runbook_url is not None
        )

        return Prioritization(
            impact_score=impact,
            urgency_score=urgency,
            effort_estimate_minutes=effort_minutes,
            solvability=solvability_level,
            composite_priority=composite_priority,
            auto_resolve_eligible=auto_resolve,
            runbook_url=runbook_url,
            rationale=" • ".join(rationale_parts) if rationale_parts else "",
            matched_rules=matched_rule_ids,
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_policy(path: Path) -> dict[str, Any]:
        if not path.exists():
            _LOGGER.warning("triage policy not found at %s — using empty policy", path)
            return {}
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    @staticmethod
    def _build_context(ticket: Ticket, analysis: TriageAnalysis) -> dict[str, Any]:
        title = (getattr(ticket, "title", "") or "").lower()
        description = (getattr(ticket, "description", "") or "").lower()
        return {
            "title": title,
            "description": description,
            "title_description": f"{title}\n{description}",
            "department": getattr(ticket, "department", "") or "",
            "ai_category": (
                getattr(analysis.predicted_category, "value", None)
                or str(getattr(analysis, "predicted_category", ""))
            ).lower(),
            "ai_priority": (
                getattr(analysis.predicted_priority, "value", None)
                or str(getattr(analysis, "predicted_priority", ""))
            ).lower(),
            "tags": _normalize_tags(getattr(ticket, "tags", None)),
        }

    def _rule_matches(self, match: dict[str, Any], context: dict[str, Any]) -> bool:
        if not match:
            return False

        if "department" in match and match["department"] != context["department"]:
            return False

        # tags_any + title_any are treated as alternative *detectors* for
        # the same intent: a rule with both fires when either matches, so
        # tag-less legacy tickets are still caught via title keywords.
        # Each criterion still acts as a hard filter when used alone.
        has_tags = "tags_any" in match
        has_title = "title_any" in match
        if has_tags or has_title:
            tag_hit = False
            title_hit = False
            if has_tags:
                wanted = {t.lower() for t in match["tags_any"]}
                tag_hit = bool(wanted.intersection(context["tags"]))
            if has_title:
                haystack = context["title_description"]
                title_hit = any(word.lower() in haystack for word in match["title_any"])
            if has_tags and has_title:
                if not (tag_hit or title_hit):
                    return False
            elif has_tags and not tag_hit or has_title and not title_hit:
                return False

        if "ai_category_any" in match:
            wanted = {c.lower() for c in match["ai_category_any"]}
            if context["ai_category"] not in wanted:
                return False

        if "ai_priority_any" in match:
            wanted = {p.lower() for p in match["ai_priority_any"]}
            if context["ai_priority"] not in wanted:
                return False

        return True

    @staticmethod
    def _clamp_score(value: Any) -> int:
        try:
            score = int(value)
        except (TypeError, ValueError):
            score = 3
        return max(1, min(5, score))

    @staticmethod
    def _parse_solvability(value: str | None) -> SolvabilityLevel:
        if value is None:
            return SolvabilityLevel.L2
        normalised = str(value).strip().lower().replace("_", "-")
        for level in SolvabilityLevel:
            if level.value == normalised:
                return level
        return SolvabilityLevel.L2

    def _estimate_effort(self, similar_cases: list[SimilarCase] | None) -> int:
        fallback = int(self._policy.get("default_effort_minutes", 60))
        if not similar_cases:
            return fallback
        observed = [
            c.effort_estimate_minutes
            for c in similar_cases
            if c.effort_estimate_minutes and c.effort_estimate_minutes > 0
        ]
        if not observed:
            return fallback
        return max(5, round(sum(observed) / len(observed)))


def _normalize_tags(raw_tags: Any) -> set[str]:
    """Tag fields are sometimes Python lists, sometimes JSON strings."""

    if raw_tags is None:
        return set()
    if isinstance(raw_tags, (list, tuple, set)):
        return {str(t).lower() for t in raw_tags}
    if isinstance(raw_tags, str):
        text = raw_tags.strip()
        if not text:
            return set()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {part.strip().lower() for part in text.split(",") if part.strip()}
        if isinstance(parsed, list):
            return {str(t).lower() for t in parsed}
    return set()
