"""Verify the global error handlers don't leak stack traces or secrets."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validation_error_uses_structured_response():
    # Body missing required title/description → 422 from FastAPI/Pydantic.
    response = client.post("/tickets/triage", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Request validation failed."
    assert isinstance(body.get("errors"), list)


def test_404_passes_through_with_generic_detail():
    response = client.get("/tickets/this-ticket-id-does-not-exist-xyz")
    # Either the get-ticket route returns 404 or routing produces 404.
    assert response.status_code == 404
    assert "stack" not in response.text.lower()
    assert "traceback" not in response.text.lower()


def test_error_responses_never_leak_traceback_keywords():
    # Force a malformed request that the route will reject via ValueError.
    response = client.post("/tickets/triage", json={"title": "ab", "description": "ab"})
    text = response.text.lower()
    for forbidden in ("traceback", 'file "/', " line ", "sqlalchemy.exc"):
        assert forbidden not in text, f"response leaks: {forbidden!r}"
