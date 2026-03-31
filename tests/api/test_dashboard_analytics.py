from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_analytics_returns_expected_structure():
    client = TestClient(app)

    triage_payload_1 = {
        "title": "Checkout fails for premium users",
        "description": "Users cannot complete checkout. Needs urgent review.",
        "reporter": "claudio",
        "source": "internal",
    }
    triage_payload_2 = {
        "title": "Need export feature for reports",
        "description": "Business wants CSV export in the analytics module.",
        "reporter": "claudio",
        "source": "internal",
    }

    triage_response_1 = client.post("/tickets/triage", json=triage_payload_1)
    triage_response_2 = client.post("/tickets/triage", json=triage_payload_2)

    assert triage_response_1.status_code == 200
    assert triage_response_2.status_code == 200

    ticket_id_1 = triage_response_1.json()["ticket_id"]

    decision_payload = {
        "ticket_id": ticket_id_1,
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "engineering-team",
        "accepted_ai_suggestion": True,
        "review_comment": "Confirmed by reviewer.",
        "reviewed_by": "claudio",
    }

    decision_response = client.post("/tickets/decision", json=decision_payload)
    assert decision_response.status_code == 200

    analytics_response = client.get("/tickets/analytics")
    assert analytics_response.status_code == 200

    body = analytics_response.json()

    assert "stats" in body
    assert "status_distribution" in body
    assert "category_distribution" in body
    assert "priority_distribution" in body
    assert "department_distribution" in body
    assert "management_metrics" in body
    assert "review_funnel" in body
    assert "ai_acceptance" in body
    assert "needs_attention" in body
    assert "recent_activity" in body

    assert body["stats"]["total"] >= 2
    assert isinstance(body["status_distribution"], list)
    assert isinstance(body["category_distribution"], list)
    assert isinstance(body["priority_distribution"], list)
    assert isinstance(body["department_distribution"], list)
    assert isinstance(body["review_funnel"], list)
    assert isinstance(body["ai_acceptance"], list)
    assert isinstance(body["needs_attention"], list)
    assert isinstance(body["recent_activity"], list)
    assert body["management_metrics"]["reviewed_count"] >= 1
