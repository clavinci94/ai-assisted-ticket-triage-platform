from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_decision_updates_ticket_status_to_reviewed():
    triage_payload = {
        "title": "Checkout failure in production",
        "description": "Users cannot complete checkout. Incident needs urgent review.",
        "reporter": "claudio",
        "source": "internal",
    }

    triage_response = client.post("/tickets/triage", json=triage_payload)
    assert triage_response.status_code == 200
    triage_body = triage_response.json()
    ticket_id = triage_body["ticket_id"]

    decision_payload = {
        "ticket_id": ticket_id,
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "engineering-team",
        "accepted_ai_suggestion": True,
        "review_comment": "Confirmed by reviewer.",
        "reviewed_by": "claudio",
    }

    decision_response = client.post("/tickets/decision", json=decision_payload)
    assert decision_response.status_code == 200

    ticket_response = client.get(f"/tickets/{ticket_id}")
    assert ticket_response.status_code == 200

    ticket_body = ticket_response.json()
    assert ticket_body["status"] == "reviewed"
    assert ticket_body["decision"] is not None
    assert ticket_body["decision"]["reviewed_by"] == "claudio"
