from app.domain.entities.triage_decision import TriageDecision
from app.domain.enums.ticket_category import TicketCategory
from app.domain.enums.ticket_priority import TicketPriority


class ReviewTriageDecisionUseCase:
    def execute(
        self,
        final_category: str,
        final_priority: str,
        final_team: str,
        accepted_ai_suggestion: bool,
        review_comment: str | None = None,
        reviewed_by: str | None = None,
    ) -> TriageDecision:
        return TriageDecision(
            final_category=TicketCategory(final_category),
            final_priority=TicketPriority(final_priority),
            final_team=final_team,
            accepted_ai_suggestion=accepted_ai_suggestion,
            review_comment=review_comment,
            reviewed_by=reviewed_by,
        )
