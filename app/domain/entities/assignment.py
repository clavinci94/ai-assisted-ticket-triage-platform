from dataclasses import dataclass


@dataclass
class Assignment:
    assigned_team: str
    assignee: str | None = None
    assigned_by: str | None = None
    assignment_note: str | None = None
