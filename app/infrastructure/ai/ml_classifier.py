from datetime import datetime, timezone

from app.application.ports.classifier_port import ClassifierPort
from app.domain.constants.departments import infer_department_from_text
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority
from app.infrastructure.ai.model_loader import load_model


class MLClassifier(ClassifierPort):
    def __init__(self, model_version: str = "tfidf-mnb-v1") -> None:
        self.model = load_model()
        self.model_version = model_version

    def analyze(self, ticket: Ticket) -> TriageAnalysis:
        if self.model is None:
            raise RuntimeError("ML-Modell nicht gefunden. Bitte trainiere das Modell zuerst.")

        text = f"{ticket.title} {ticket.description}"
        probabilities = self.model.predict_proba([text])[0]
        label = self.model.classes_[probabilities.argmax()]
        confidence = float(probabilities.max())

        category = self._map_label_to_category(label)
        priority = self._infer_priority(ticket, category)
        department = infer_department_from_text(text, fallback=ticket.department)
        suggested_team = self._infer_team(category)
        next_step = self._infer_next_step(category)
        rationale = f"ML-Klassifikation mit TF-IDF + MultinomialNB. Vorhergesagtes Label: {label}"
        summary = f"Triage-Analyse für Ticket: {ticket.title}"

        return TriageAnalysis(
            predicted_category=category,
            category_confidence=confidence,
            predicted_priority=priority,
            priority_confidence=confidence,
            summary=summary,
            suggested_team=suggested_team,
            suggested_department=department,
            next_step=next_step,
            rationale=rationale,
            model_version=self.model_version,
            analyzed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def _map_label_to_category(self, label: str) -> TicketCategory:
        normalized = label.strip().lower()

        if normalized == "bug":
            return TicketCategory.BUG
        if normalized == "feature":
            return TicketCategory.FEATURE
        if normalized == "support":
            return TicketCategory.SUPPORT
        if normalized == "requirement":
            return TicketCategory.REQUIREMENT
        if normalized == "question":
            return TicketCategory.QUESTION

        return TicketCategory.UNKNOWN

    def _infer_priority(self, ticket: Ticket, category: TicketCategory) -> TicketPriority:
        text = f"{ticket.title} {ticket.description}".lower()

        if any(word in text for word in ["critical", "outage", "production down", "data loss", "security"]):
            return TicketPriority.HIGH

        if category == TicketCategory.BUG:
            return TicketPriority.HIGH
        if category in {TicketCategory.FEATURE, TicketCategory.REQUIREMENT}:
            return TicketPriority.MEDIUM
        if category in {TicketCategory.SUPPORT, TicketCategory.QUESTION}:
            return TicketPriority.MEDIUM

        return TicketPriority.MEDIUM

    def _infer_team(self, category: TicketCategory) -> str:
        # In this banking IT support environment, all tickets are routed to the IT support area.
        return "it-support-team"

    def _infer_next_step(self, category: TicketCategory) -> str:
        if category == TicketCategory.BUG:
            return "Problem reproduzieren und Logs sammeln."
        if category in {TicketCategory.FEATURE, TicketCategory.REQUIREMENT}:
            return "Fachlichen Nutzen prüfen und Akzeptanzkriterien klären."
        if category in {TicketCategory.SUPPORT, TicketCategory.QUESTION}:
            return "Fehlenden Kontext einholen und die meldende Person begleiten."
        return "Ticket manuell prüfen."
