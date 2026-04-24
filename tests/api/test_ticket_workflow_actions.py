from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_ticket(title: str) -> str:
    response = client.post(
        "/tickets/triage",
        json={
            "title": title,
            "description": "Workflow-Aktionen sollen an diesem Ticket geprüft werden.",
            "reporter": "claudio",
            "source": "internal",
        },
    )
    assert response.status_code == 200
    return response.json()["ticket_id"]


def test_status_endpoint_can_close_ticket_and_log_note():
    ticket_id = _create_ticket("Workflow Close Test")

    status_response = client.post(
        "/tickets/status",
        json={
            "ticket_id": ticket_id,
            "status": "closed",
            "actor": "claudio",
            "note": "Manuell abgeschlossen nach Rückmeldung aus dem Betrieb.",
        },
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "closed"

    ticket_response = client.get(f"/tickets/{ticket_id}")
    assert ticket_response.status_code == 200
    ticket_body = ticket_response.json()

    assert ticket_body["status"] == "closed"
    assert any(
        event["event_type"] == "status_changed" and "Manuell abgeschlossen" in (event.get("details") or "")
        for event in ticket_body["events"]
    )


def test_comment_endpoint_adds_comment_and_internal_note_events():
    ticket_id = _create_ticket("Workflow Comment Test")

    comment_response = client.post(
        "/tickets/comments",
        json={
            "ticket_id": ticket_id,
            "actor": "claudio",
            "body": "Bitte Rückmeldung aus dem Fachbereich einholen.",
            "is_internal": False,
        },
    )
    assert comment_response.status_code == 200

    note_response = client.post(
        "/tickets/comments",
        json={
            "ticket_id": ticket_id,
            "actor": "claudio",
            "body": "Interne Notiz: VIP-Fall mit erhöhter Aufmerksamkeit.",
            "is_internal": True,
        },
    )
    assert note_response.status_code == 200

    ticket_response = client.get(f"/tickets/{ticket_id}")
    assert ticket_response.status_code == 200
    events = ticket_response.json()["events"]

    assert any(
        event["event_type"] == "comment_added"
        and event["details"] == "Bitte Rückmeldung aus dem Fachbereich einholen."
        for event in events
    )
    assert any(
        event["event_type"] == "internal_note_added" and "VIP-Fall" in (event.get("details") or "")
        for event in events
    )


def test_escalation_endpoint_sets_priority_team_assignee_and_sla():
    ticket_id = _create_ticket("Workflow Escalation Test")

    escalation_response = client.post(
        "/tickets/escalate",
        json={
            "ticket_id": ticket_id,
            "escalated_by": "claudio",
            "reason": "Kundenauswirkung hoch und SLA akut gefährdet.",
            "target_team": "incident-response-team",
            "assignee": "maria",
            "priority": "critical",
        },
    )
    assert escalation_response.status_code == 200

    ticket_response = client.get(f"/tickets/{ticket_id}")
    assert ticket_response.status_code == 200
    ticket_body = ticket_response.json()

    assert ticket_body["priority"] == "critical"
    assert ticket_body["team"] == "incident-response-team"
    assert ticket_body["assignee"] == "maria"
    assert ticket_body["sla_breached"] is True
    assert any(event["event_type"] == "ticket_escalated" for event in ticket_body["events"])
