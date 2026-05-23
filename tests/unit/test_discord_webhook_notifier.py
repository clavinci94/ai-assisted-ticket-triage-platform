import json
import urllib.error
import urllib.request

import pytest

from app.domain.entities.escalation_notification import EscalationNotification
from app.infrastructure.notifications.discord_webhook_notifier import DiscordWebhookNotifier
from app.infrastructure.notifications.null_notifier import NullNotifier


class _FakeResponse:
    status = 204

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _notification(**overrides) -> EscalationNotification:
    base = {
        "ticket_id": "DEMO-042",
        "title": "AML-Verdacht auf Konto",
        "priority": "critical",
        "reason": "Regulatorisches Risiko, sofortige Eskalation.",
        "escalated_by": "claudio",
        "team": "compliance-team",
        "assignee": "maria",
    }
    base.update(overrides)
    return EscalationNotification(**base)


def test_discord_notifier_posts_discord_shaped_payload(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["method"] = request.method
        captured["headers"] = request.headers
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    notifier = DiscordWebhookNotifier("https://discord.com/api/webhooks/x/y", timeout_seconds=3)
    notifier.notify_escalation(_notification())

    assert captured["url"] == "https://discord.com/api/webhooks/x/y"
    assert captured["method"] == "POST"
    assert captured["headers"]["Content-type"] == "application/json"
    assert captured["timeout"] == 3

    body = captured["body"]
    assert "DEMO-042" in body["content"]
    embed = body["embeds"][0]
    assert "AML-Verdacht auf Konto" in embed["title"]
    field_names = {field["name"] for field in embed["fields"]}
    assert {"Priorität", "Zielteam", "Bearbeitung", "Eskaliert von", "Grund"} <= field_names


def test_discord_notifier_omits_empty_optional_fields(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    notifier = DiscordWebhookNotifier("https://discord.com/api/webhooks/x/y")
    notifier.notify_escalation(_notification(team=None, assignee=None, escalated_by=None))

    field_names = {field["name"] for field in captured["body"]["embeds"][0]["fields"]}
    assert field_names == {"Priorität", "Grund"}


def test_discord_notifier_propagates_delivery_failure(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    notifier = DiscordWebhookNotifier("https://discord.com/api/webhooks/x/y")

    # The adapter does not swallow — the use case owns best-effort handling.
    with pytest.raises(urllib.error.URLError):
        notifier.notify_escalation(_notification())


def test_discord_notifier_requires_url():
    with pytest.raises(ValueError, match="requires a webhook URL"):
        DiscordWebhookNotifier("")


def test_null_notifier_makes_no_network_call(monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("NullNotifier must not touch the network")

    monkeypatch.setattr(urllib.request, "urlopen", explode)

    NullNotifier().notify_escalation(_notification())
