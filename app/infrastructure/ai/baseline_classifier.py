from datetime import datetime

from app.application.ports.classifier_port import ClassifierPort
from app.domain.constants.departments import infer_department_from_text
from app.domain.entities.similar_case import SimilarCase
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority


class BaselineClassifier(ClassifierPort):
    def analyze(
        self,
        ticket: Ticket,
        similar_cases: list[SimilarCase] | None = None,  # noqa: ARG002 — retrieval context not used by baseline heuristic
    ) -> TriageAnalysis:
        context_parts = [
            ticket.title,
            ticket.description,
            ticket.category or "",
            ticket.priority or "",
            ticket.team or "",
            ticket.assignee or "",
            " ".join(ticket.tags),
        ]
        text = " ".join(part for part in context_parts if part).lower()
        department = infer_department_from_text(text, fallback=ticket.department)

        category = TicketCategory.REQUIREMENT
        priority = TicketPriority.MEDIUM
        suggested_team = "it-support-team"
        next_step = "Anforderung prüfen und Akzeptanzkriterien klären."
        rationale = "Baseline-Heuristik auf Basis von Stichwörtern in Titel und Beschreibung."

        if any(word in text for word in ["error", "crash", "bug", "fails", "failure"]):
            category = TicketCategory.BUG
            priority = TicketPriority.HIGH
            suggested_team = "it-support-team"
            next_step = "Problem reproduzieren und Logs sammeln."
            rationale = "Fehlerbezogene Stichwörter wurden erkannt."
        elif any(word in text for word in ["help", "support", "how to", "question"]):
            category = TicketCategory.SUPPORT
            priority = TicketPriority.MEDIUM
            suggested_team = "it-support-team"
            next_step = "Fehlenden Kontext einholen und die meldende Person begleiten."
            rationale = "Supportbezogene Stichwörter wurden erkannt."
        elif any(word in text for word in ["feature", "add", "enhancement", "improve"]):
            category = TicketCategory.FEATURE
            priority = TicketPriority.MEDIUM
            suggested_team = "it-support-team"
            next_step = "Fachlichen Nutzen prüfen und Business Value einschätzen."
            rationale = "Featurebezogene Stichwörter wurden erkannt."

        summary = f"Triage-Analyse für Ticket: {ticket.title}"

        return TriageAnalysis(
            predicted_category=category,
            category_confidence=0.70,
            predicted_priority=priority,
            priority_confidence=0.65,
            summary=summary,
            suggested_team=suggested_team,
            suggested_department=department,
            next_step=next_step,
            rationale=rationale,
            model_version="baseline-v1",
            analyzed_at=datetime.utcnow(),
        )
