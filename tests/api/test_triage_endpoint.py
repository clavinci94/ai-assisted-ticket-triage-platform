from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_triage_endpoint_returns_audit_metadata():
    payload = {
        "title": "Login outage in production",
        "description": "All users receive 500 errors during login. Possible production down incident.",
        "reporter": "claudio",
        "source": "internal",
    }

    response = client.post("/tickets/triage", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert "ticket_id" in body
    assert "analysis" in body

    analysis = body["analysis"]
    assert analysis["predicted_category"] in {
        "bug",
        "feature",
        "support",
        "requirement",
        "question",
        "unknown",
    }
    assert "model_version" in analysis
    assert analysis["model_version"] == "tfidf-mnb-v1"
    assert "analyzed_at" in analysis
    assert isinstance(analysis["analyzed_at"], str)
    assert analysis["analyzed_at"].endswith("Z")
