from enum import Enum


class TicketCategory(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    SUPPORT = "support"
    REQUIREMENT = "requirement"
    QUESTION = "question"
    UNKNOWN = "unknown"
