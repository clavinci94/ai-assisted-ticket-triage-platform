from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ticket_workbench_supports_search_filter_and_pagination():
    prefix = f"WB-PAGE-CLAUDIO-{uuid4().hex[:8]}"

    payloads = [
        {
            "title": f"{prefix} Alpha",
            "description": "Erster Vorgang für Pagination und Filter.",
            "reporter": "claudio",
            "source": "internal",
        },
        {
            "title": f"{prefix} Bravo",
            "description": "Zweiter Vorgang für Pagination und Filter.",
            "reporter": "claudio",
            "source": "internal",
        },
        {
            "title": f"{prefix} Charlie",
            "description": "Dritter Vorgang wird später zugewiesen.",
            "reporter": "claudio",
            "source": "internal",
        },
    ]

    ticket_ids = []
    for payload in payloads:
        triage_response = client.post("/tickets/triage", json=payload)
        assert triage_response.status_code == 200
        ticket_ids.append(triage_response.json()["ticket_id"])

    decision_response = client.post(
        "/tickets/decision",
        json={
            "ticket_id": ticket_ids[2],
            "final_category": "bug",
            "final_priority": "medium",
            "final_team": "operations-team",
            "accepted_ai_suggestion": True,
            "review_comment": "Für Pagination-Test überprüft.",
            "reviewed_by": "claudio",
        },
    )
    assert decision_response.status_code == 200

    assignment_response = client.post(
        "/tickets/assign",
        json={
            "ticket_id": ticket_ids[2],
            "assigned_team": "operations-team",
            "assigned_by": "claudio",
            "assignment_note": "Zugewiesen für Filtertest.",
        },
    )
    assert assignment_response.status_code == 200

    response = client.get(
        "/tickets/workbench",
        params={
            "q": prefix,
            "status": "triaged",
            "page": 1,
            "page_size": 1,
            "sort_by": "title",
            "sort_dir": "asc",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["total_pages"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == f"{prefix} Alpha"
    assert body["items"][0]["status"] == "triaged"
    assert "triaged" in body["facets"]["statuses"]


def test_ticket_workbench_supports_mine_and_escalations_views():
    prefix = f"WB-VIEWS-CLAUDIO-{uuid4().hex[:8]}"

    triage_claudio = client.post(
        "/tickets/triage",
        json={
            "title": f"{prefix} Kritisch",
            "description": "Dieser Vorgang soll in der Eskalationssicht landen.",
            "reporter": "claudio",
            "source": "internal",
        },
    )
    assert triage_claudio.status_code == 200
    claudio_ticket_id = triage_claudio.json()["ticket_id"]

    triage_alice = client.post(
        "/tickets/triage",
        json={
            "title": f"{prefix} Normal",
            "description": "Dieser Vorgang gehört nicht in die persönliche Sicht von Claudio.",
            "reporter": "alice",
            "source": "internal",
        },
    )
    assert triage_alice.status_code == 200
    alice_ticket_id = triage_alice.json()["ticket_id"]

    claudio_decision = client.post(
        "/tickets/decision",
        json={
            "ticket_id": claudio_ticket_id,
            "final_category": "bug",
            "final_priority": "critical",
            "final_team": "incident-team",
            "accepted_ai_suggestion": True,
            "review_comment": "Kritischer Vorgang für Eskalationssicht.",
            "reviewed_by": "claudio",
        },
    )
    assert claudio_decision.status_code == 200

    alice_decision = client.post(
        "/tickets/decision",
        json={
            "ticket_id": alice_ticket_id,
            "final_category": "support",
            "final_priority": "low",
            "final_team": "service-desk",
            "accepted_ai_suggestion": True,
            "review_comment": "Niedrige Priorität.",
            "reviewed_by": "alice",
        },
    )
    assert alice_decision.status_code == 200

    mine_response = client.get(
        "/tickets/workbench",
        params={
            "q": prefix,
            "view": "mine",
            "operator": "claudio",
        },
    )
    assert mine_response.status_code == 200
    mine_body = mine_response.json()

    assert mine_body["total"] >= 1
    assert all(item["reporter"] == "claudio" or item["assignee"] == "claudio" for item in mine_body["items"])

    escalations_response = client.get(
        "/tickets/workbench",
        params={
            "q": prefix,
            "view": "escalations",
        },
    )
    assert escalations_response.status_code == 200
    escalations_body = escalations_response.json()

    assert escalations_body["total"] == 1
    assert escalations_body["items"][0]["ticket_id"] == claudio_ticket_id
    assert escalations_body["items"][0]["priority"] == "critical"
