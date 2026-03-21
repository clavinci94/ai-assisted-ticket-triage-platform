from datetime import datetime
from app.application.ports.classifier_port import ClassifierPort
from app.domain.entities.ticket import Ticket
from app.domain.entities.triage_analysis import TriageAnalysis
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority


class BaselineClassifier(ClassifierPort):
    def analyze(self, ticket: Ticket) -> TriageAnalysis:
        text = f"{ticket.title} {ticket.description}".lower()

        category = TicketCategory.REQUIREMENT
        priority = TicketPriority.MEDIUM
        suggested_team = "product-team"
        next_step = "Review the requirement and clarify acceptance criteria."
        rationale = "Baseline heuristic based on title and description keywords."

        if any(word in text for word in ["error", "crash", "bug", "fails", "failure"]):
            category = TicketCategory.BUG
            priority = TicketPriority.HIGH
            suggested_team = "engineering-team"
            next_step = "Reproduce the issue and collect logs."
            rationale = "Detected bug-related keywords."
        elif any(word in text for word in ["help", "support", "how to", "question"]):
            category = TicketCategory.SUPPORT
            priority = TicketPriority.MEDIUM
            suggested_team = "support-team"
            next_step = "Request missing context and guide the user."
            rationale = "Detected support-related keywords."
        elif any(word in text for word in ["feature", "add", "enhancement", "improve"]):
            category = TicketCategory.FEATURE
            priority = TicketPriority.MEDIUM
            suggested_team = "product-team"
            next_step = "Review product fit and estimate business value."
            rationale = "Detected feature-related keywords."

        summary = f"Triage analysis for ticket: {ticket.title}"

        return TriageAnalysis(
            predicted_category=category,
            category_confidence=0.70,
            predicted_priority=priority,
            priority_confidence=0.65,
            summary=summary,
            suggested_team=suggested_team,
            next_step=next_step,
            rationale=rationale,
        )
