import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_triage_endpoint_routes_ticket_using_litellm(monkeypatch):
    payload = {
        "title": "Password reset request",
        "description": "Customer cannot access account and needs access. This looks like a support routing issue.",
        "reporter": "claudio",
        "source": "internal",
    }

    def fake_completion(
        model,
        messages,
        temperature=None,
        max_tokens=None,
        api_key=None,
        api_base=None,
        api_version=None,
        **kwargs,
    ):
        return type(
            "Response",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "message": type(
                                "Message",
                                (),
                                {
                                    "content": json.dumps(
                                        {
                                            "category": "support",
                                            "priority": "medium",
                                            "suggested_team": "support-team",
                                            "suggested_department": "Digital Channels",
                                            "summary": "LLM recommended support routing.",
                                            "next_step": "Verify account and reset credentials.",
                                            "rationale": "The ticket describes an urgent account access issue best handled by support.",
                                        }
                                    )
                                },
                            )
                        },
                    )
                ]
            },
        )

    monkeypatch.setattr("app.infrastructure.ai.litellm_classifier.completion", fake_completion)
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("LITELLM_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-api-key")
    monkeypatch.setenv("AZURE_API_BASE", "https://example.services.ai.azure.com/models")

    response = client.post("/tickets/triage/llm", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["final_team"] == "support-team"
    assert body["final_category"] == "support"
    assert body["final_priority"] == "medium"
    assert body["analysis"]["suggested_department"] == "Digital Channels"
    assert (
        body["analysis"]["rationale"]
        == "The ticket describes an urgent account access issue best handled by support."
    )
    assert body["analysis"]["model_version"].startswith("litellm-")

    ticket_response = client.get(f"/tickets/{body['ticket_id']}")
    assert ticket_response.status_code == 200
    assert ticket_response.json()["department"] == "Digital Channels"


def test_llm_preview_endpoint_returns_department_recommendation_without_persisting(monkeypatch):
    payload = {
        "title": "Mobile Banking Login schlägt fehl",
        "description": "Kundinnen können sich in der Mobile-App nicht mehr anmelden.",
        "reporter": "claudio",
        "source": "internal",
    }

    def fake_completion(
        model,
        messages,
        temperature=None,
        max_tokens=None,
        api_key=None,
        api_base=None,
        api_version=None,
        **kwargs,
    ):
        return type(
            "Response",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "message": type(
                                "Message",
                                (),
                                {
                                    "content": json.dumps(
                                        {
                                            "category": "support",
                                            "priority": "medium",
                                            "suggested_team": "support-team",
                                            "suggested_department": "Digital Channels",
                                            "summary": "Login issue in mobile banking.",
                                            "next_step": "Review app access logs.",
                                            "rationale": "The issue affects a digital customer channel.",
                                        }
                                    )
                                },
                            )
                        },
                    )
                ]
            },
        )

    monkeypatch.setattr("app.infrastructure.ai.litellm_classifier.completion", fake_completion)
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("LITELLM_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-api-key")
    monkeypatch.setenv("AZURE_API_BASE", "https://example.services.ai.azure.com/models")

    before_count = len(client.get("/tickets").json())
    response = client.post("/tickets/triage/llm/preview", json=payload)
    after_count = len(client.get("/tickets").json())

    assert response.status_code == 200
    body = response.json()

    assert body["suggested_department"] == "Digital Channels"
    assert body["rationale"] == "The issue affects a digital customer channel."
    assert before_count == after_count


def test_llm_triage_endpoint_uses_litellm_proxy(monkeypatch):
    payload = {
        "title": "VPN-Zugang funktioniert nicht",
        "description": "Der Benutzer kann sich seit heute Morgen nicht mehr verbinden.",
        "reporter": "claudio",
        "source": "internal",
    }

    class FakeCompletions:
        @staticmethod
        def create(model, messages, temperature=None, max_tokens=None, response_format=None):
            assert model == "azure_ai/gpt-oss-120b"
            assert response_format == {"type": "json_object"}
            return type(
                "Response",
                (),
                {
                    "choices": [
                        type(
                            "Choice",
                            (),
                            {
                                "message": type(
                                    "Message",
                                    (),
                                    {
                                        "content": json.dumps(
                                            {
                                                "category": "support",
                                                "priority": "medium",
                                                "suggested_team": "support-team",
                                                "suggested_department": "Bank-IT Support",
                                                "summary": "Proxy-Routing erfolgreich.",
                                                "next_step": "Zugang prüfen.",
                                                "rationale": "Der Proxy liefert einen gültigen JSON-Response.",
                                            }
                                        )
                                    },
                                )
                            },
                        )
                    ]
                },
            )

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, api_key, base_url):
            assert api_key == "dummy-proxy-key"
            assert base_url == "http://127.0.0.1:4000"
            self.chat = FakeChat()

    monkeypatch.setattr("app.infrastructure.ai.litellm_classifier.OpenAI", FakeOpenAI)
    monkeypatch.delenv("AZURE_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LITELLM_API_KEY", "dummy-proxy-key")
    monkeypatch.setenv("LITELLM_API_BASE", "http://127.0.0.1:4000")

    response = client.post("/tickets/triage/llm", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["final_team"] == "support-team"
    assert body["analysis"]["summary"] == "Proxy-Routing erfolgreich."
    assert body["analysis"]["suggested_department"] == "Bank-IT Support"


def test_llm_triage_endpoint_keeps_manual_department_override(monkeypatch):
    payload = {
        "title": "SEPA-Buchungen doppelt",
        "description": "Zahlungen werden doppelt verbucht und Kundinnen reklamieren bereits.",
        "reporter": "claudio",
        "source": "internal",
        "department": "Risk & Compliance",
        "department_locked": True,
    }

    def fake_completion(
        model,
        messages,
        temperature=None,
        max_tokens=None,
        api_key=None,
        api_base=None,
        api_version=None,
        **kwargs,
    ):
        return type(
            "Response",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "message": type(
                                "Message",
                                (),
                                {
                                    "content": json.dumps(
                                        {
                                            "category": "bug",
                                            "priority": "high",
                                            "suggested_team": "support-team",
                                            "suggested_department": "Payments Operations",
                                            "summary": "Duplicate payment postings detected.",
                                            "next_step": "Inspect payment processing logs.",
                                            "rationale": "The incident belongs operationally to payments.",
                                        }
                                    )
                                },
                            )
                        },
                    )
                ]
            },
        )

    monkeypatch.setattr("app.infrastructure.ai.litellm_classifier.completion", fake_completion)
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("LITELLM_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-api-key")
    monkeypatch.setenv("AZURE_API_BASE", "https://example.services.ai.azure.com/models")

    response = client.post("/tickets/triage/llm", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["analysis"]["suggested_department"] == "Payments Operations"

    ticket_response = client.get(f"/tickets/{body['ticket_id']}")
    assert ticket_response.status_code == 200
    ticket_body = ticket_response.json()
    assert ticket_body["department"] == "Risk & Compliance"
    assert ticket_body["analysis"]["suggested_department"] == "Payments Operations"
