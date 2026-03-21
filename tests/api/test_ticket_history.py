from fastapi.testclient import TestClient

from app.main import app


def test_ticket_history_contains_triage_review_assignment_events():
    client = TestClient(app)

    triage_payload = {
        "title": "Checkout fails after payment redirect",
        "description": "Users return from PSP and checkout remains stuck.",
        "reporter": "claudio",
        "source": "internal",
    }

    triage_response = client.post("/tickets/triage", json=triage_payload)
    assert triage_response.status_code == 200
    ticket_id = triage_response.json()["ticket_id"]

    decision_payload = {
        "ticket_id": ticket_id,
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "engineering-team",
        "accepted_ai_suggestion": True,
        "review_comment": "Confirmed production issue.",
        "reviewed_by": "claudio",
    }
    decision_response = client.post("/tickets/decision", json=decision_payload)
    assert decision_response.status_code == 200

    assignment_payload = {
        "ticket_id": ticket_id,
        "assigned_team": "engineering-team",
        "assigned_by": "claudio",
        "assignment_note": "Escalated to backend squad.",
    }
    assignment_response = client.post("/tickets/assign", json=assignment_payload)
    assert assignment_response.status_code == 200

    ticket_response = client.get(f"/tickets/{ticket_id}")
    assert ticket_response.status_code == 200

    body = ticket_response.json()
    events = body["events"]

    assert isinstance(events, list)
    assert len(events) >= 4

    event_types = [event["event_type"] for event in events]
    assert "ticket_created" in event_types
    assert "triage_completed" in event_types
    assert "review_saved" in event_types
    assert "assignment_saved" in event_types
