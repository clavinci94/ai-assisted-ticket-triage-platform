# ADR 0005: Outbound escalation notifications via a notifier port

- **Status:** Accepted
- **Date:** 2026-05-23
- **Decision makers:** Core team
- **Related:** [ADR 0001 (Clean Architecture)](./0001-clean-architecture.md)

## Context

When an operator escalates a ticket (`POST /tickets/escalate`), the
platform does three things: it raises the priority, reassigns the ticket,
and writes a `ticket_escalated` audit event. All three are *inward* —
they change state that someone has to come looking for. Nobody is
actively told that a ticket just became critical.

In practice the on-call team finds out about an escalation when they next
refresh the dashboard. For a platform whose whole point is to move the
urgent work to the front of the queue, "poll the dashboard to discover
the emergency" is the wrong default. The team already coordinates in a
Discord channel; they want the escalation to land there the moment it
happens.

This was on the roadmap as *"Webhook outbound integration (Slack / Teams)
for escalations"*. The constraint is the same one that shaped every other
external dependency in this codebase: it must be **swappable, testable,
and impossible to let take down the core flow.**

## Decision

Introduce an outbound **notification step** that runs after a successful
escalation, behind a new `NotificationPort`:

```
HTTP route  /tickets/escalate
   └── EscalateTicketUseCase
         ├── repository.update_ticket_fields(...)   (unchanged)
         ├── repository.add_event("ticket_escalated") (unchanged)
         └── notifier.notify_escalation(EscalationNotification)   ← new, best-effort
```

The port has a single method:

```python
class NotificationPort(ABC):
    @abstractmethod
    def notify_escalation(self, notification: EscalationNotification) -> None: ...
```

`EscalationNotification` is a pure domain dataclass carrying exactly what a
reader needs to act — ticket id, title, new priority, team, assignee,
reason, who escalated, and when. **Rendering is the adapter's job, not the
entity's** — the entity stays transport-agnostic so a future email or
Microsoft Teams adapter reuses it unchanged.

Two adapters ship in v1:

- **`DiscordWebhookNotifier`** — POSTs a Discord-flavoured JSON payload
  (`{"content": ..., "embeds": [...]}`) to an incoming-webhook URL using
  the standard library's `urllib.request`. The embed renders the
  escalation as a red-sidebar card with the reason and assignment as
  fields. No new dependency: the corpus already avoids pulling `requests`
  or `httpx` into runtime.
- **`NullNotifier`** — a no-op. It is the default when no webhook URL is
  configured, so local dev and the test suite never make a network call
  and escalation works out of the box with zero setup.

The adapter is selected once, by configuration: if
`ESCALATION_WEBHOOK_URL` is set, the route injects a `DiscordWebhookNotifier`;
otherwise a `NullNotifier`. The use case accepts the notifier as an
optional constructor argument (`notifier: NotificationPort | None = None`)
and treats `None` as "no notifications" — so every existing caller and
test keeps working untouched.

### Best-effort by contract

`notify_escalation` is called inside a `try/except` in the use case. **A
failing webhook (timeout, 4xx, DNS error) is logged and swallowed — it
never propagates.** Escalation is a state change that must succeed even
when Discord is down; a missed chat message is recoverable, a refused
escalation is not. This mirrors the graceful-degradation rule the RAG
layer follows in [ADR 0004](./0004-retrieval-augmented-triage.md).

## Why not Slack first?

The team coordinates on Discord, so Discord's payload shape (`content` +
`embeds`) is the v1 target rather than Slack's (`text` + `blocks`). The
two formats differ only in the adapter; the port and entity are identical.
A `SlackWebhookNotifier` or `TeamsWebhookNotifier` is a single new class
implementing `NotificationPort` — no change to the use case, route, or
entity. We deliberately did **not** build an abstraction that tries to
emit "universal" JSON for every chat platform: that always leaks the
lowest common denominator and renders badly everywhere.

## Why not a message queue / event bus?

Considered (publish escalation events to a broker, let subscribers fan
out). Rejected for v1:

- **Operationally heavy.** A broker is another service to run, monitor,
  and pay for on the Render free tier, for a single fire-and-forget
  message.
- **The failure mode we care about is already handled.** Best-effort
  delivery with a logged failure is exactly what a chat notification
  warrants; we don't need at-least-once delivery guarantees for "FYI, a
  ticket got hot."
- **The port stays stable.** If outbound volume ever justifies a queue,
  it becomes a `QueueNotifier` adapter behind the same port — the use
  case never learns the difference.

## Consequences

**Positive**
- Escalations reach the team where they already are, the moment they
  happen — no dashboard polling.
- Zero new runtime dependencies (`urllib.request` is stdlib).
- The notifier is fully swappable: Slack, Teams, email, or a queue are
  each one adapter behind an unchanged port.
- Failure-isolated: a webhook outage can never block or fail an
  escalation.
- Secure-by-default and zero-config: no URL → `NullNotifier` → no network
  call, so dev and CI stay hermetic.

**Negative**
- **No delivery guarantee.** If the webhook is down, the message is lost
  (the audit event still records the escalation, so nothing is silently
  forgotten — it just isn't pushed). Acceptable for a chat FYI.
- **Synchronous send.** The POST happens inline in the request with a
  short timeout. At escalation volumes this is negligible; if it ever
  isn't, the send moves to a background task without touching the port.
- **One channel.** v1 posts to a single configured webhook. Per-team
  routing is a future enhancement (a `Mapping[str, NotificationPort]` or
  a routing adapter), again behind the same port.

## Implementation notes

- Domain object: `EscalationNotification`
  (`app/domain/entities/escalation_notification.py`) — frozen dataclass,
  no framework imports.
- Port: `NotificationPort`
  (`app/application/ports/notification_port.py`) — one method.
- Adapters: `app/infrastructure/notifications/` —
  `DiscordWebhookNotifier`, `NullNotifier`.
- Config: `ESCALATION_WEBHOOK_URL` (and optional
  `ESCALATION_WEBHOOK_TIMEOUT_SECONDS`, default 5). Read in
  `ApiSettings`; the route picks the adapter via a `get_notifier`
  dependency.
- The use case treats `notifier=None` as "no notifications", keeping the
  change backwards-compatible.

## Testing

- **Unit**: `tests/unit/test_discord_webhook_notifier.py` — payload shape
  and the network call are asserted with `urllib.request.urlopen` mocked;
  a failing send is verified to raise from the adapter (the use case, not
  the adapter, owns swallowing).
- **Application**: `tests/application/test_escalate_ticket_use_case.py` —
  a `FakeNotifier` proves the use case calls `notify_escalation` with the
  right `EscalationNotification`, that a raising notifier does **not**
  break escalation, and that `notifier=None` is a no-op.
- **API**: `tests/api/test_escalation_notification.py` — the notifier is
  monkeypatched to capture, proving an escalation through the HTTP surface
  triggers exactly one notification carrying the ticket's new state.
