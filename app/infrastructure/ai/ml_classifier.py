from datetime import datetime, timezone

from app.application.ports.classifier_port import ClassifierPort
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
            raise RuntimeError("ML model not found. Train the model first.")

        text = f"{ticket.title} {ticket.description}"
        probabilities = self.model.predict_proba([text])[0]
        label = self.model.classes_[probabilities.argmax()]
        confidence = float(probabilities.max())

        category = self._map_label_to_category(label)
        priority = self._infer_priority(ticket, category)
        suggested_team = self._infer_team(category)
        next_step = self._infer_next_step(category)
        rationale = f"ML classification using TF-IDF + MultinomialNB. Predicted label: {label}"
        summary = f"Triage analysis for ticket: {ticket.title}"

        return TriageAnalysis(
            predicted_category=category,
            category_confidence=confidence,
            predicted_priority=priority,
            priority_confidence=confidence,
            summary=summary,
            suggested_team=suggested_team,
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
        if category == TicketCategory.BUG:
            return "engineering-team"
        if category in {TicketCategory.FEATURE, TicketCategory.REQUIREMENT}:
            return "product-team"
        if category in {TicketCategory.SUPPORT, TicketCategory.QUESTION}:
            return "support-team"
        return "triage-team"

    def _infer_next_step(self, category: TicketCategory) -> str:
        if category == TicketCategory.BUG:
            return "Reproduce the issue and collect logs."
        if category in {TicketCategory.FEATURE, TicketCategory.REQUIREMENT}:
            return "Review business value and clarify acceptance criteria."
        if category in {TicketCategory.SUPPORT, TicketCategory.QUESTION}:
            return "Request missing context and guide the reporter."
        return "Review ticket manually."
