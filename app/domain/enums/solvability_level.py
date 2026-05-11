from enum import Enum


class SolvabilityLevel(str, Enum):
    """How much human involvement a ticket needs to be resolved.

    ``self_service`` and ``l1`` are the levers for the early-intercept story:
    if the ticket is self-service-eligible and AI confidence is high enough,
    we can hand the user a runbook URL instead of a queue slot.
    """

    SELF_SERVICE = "self-service"
    L1 = "l1"
    L2 = "l2"
    SPECIALIST = "specialist"
