from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_triage_endpoint_persists_extended_ticket_metadata():
    payload = {
        "title": "SLA-relevanter Vorfall im E-Banking",
        "description": "Ein priorisierter Fall mit zusätzlicher Metadaten-Erfassung.",
        "reporter": "claudio",
        "source": "external",
        "category": "support",
        "priority": "high",
        "team": "Digital Channels Squad",
        "assignee": "claudio",
        "due_at": "2026-04-02T09:30:00",
        "tags": ["VIP", "E-Banking", "SLA"],
        "sla_breached": True,
    }

    triage_response = client.post("/tickets/triage", json=payload)
    assert triage_response.status_code == 200
    ticket_id = triage_response.json()["ticket_id"]

    ticket_response = client.get(f"/tickets/{ticket_id}")
    assert ticket_response.status_code == 200
    body = ticket_response.json()

    assert body["category"] == "support"
    assert body["priority"] == "high"
    assert body["team"] == "Digital Channels Squad"
    assert body["assignee"] == "claudio"
    assert body["sla_breached"] is True
    assert body["tags"] == ["VIP", "E-Banking", "SLA"]
    assert body["due_at"].startswith("2026-04-02T09:30:00")
