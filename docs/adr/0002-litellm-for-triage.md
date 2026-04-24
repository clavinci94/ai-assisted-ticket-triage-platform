# ADR 0002: LiteLLM proxy for AI-assisted triage

- **Status:** Accepted
- **Date:** 2026-04-24
- **Decision makers:** Core team

## Context

The core product promise is that the platform **suggests** — not dictates — a
department, category and priority for every incoming ticket, with a short
German-language rationale a human can verify in seconds.

Two constraints shape the implementation:

1. **Model mobility.** Bank-hosted infrastructure means the specific model
   provider (Azure AI, self-hosted, OpenAI) can change with short notice.
2. **Credential isolation.** Real API keys live in the bank's LiteLLM proxy,
   never in application code or `.env` files checked into git.

## Decision

We use the **LiteLLM proxy as the single integration surface**, talking to
it through the OpenAI-compatible `openai` Python SDK. The adapter lives in
`app/infrastructure/ai/litellm_classifier.py` and implements
`application.ports.classifier_port.ClassifierPort`.

- The proxy base URL and key are read from `LITELLM_API_BASE` /
  `LITELLM_API_KEY` (with `OPENAI_BASE_URL` / `OPENAI_API_KEY` as drop-in
  aliases). The model name is configured via `LITELLM_MODEL`.
- When the proxy is unreachable or returns malformed JSON, we **do not**
  fail the triage — we salvage known fields via `_recover_partial_json()`
  and fall back to sensible defaults. Ticket intake must never hard-fail
  because the LLM had a bad day.
- The ML classifier (`ml_classifier.py`) is kept as a second adapter for
  offline / unit-test use and as a reference implementation.

## Consequences

**Positive**
- Zero vendor lock-in at the application layer: every caller depends on
  `ClassifierPort`, not on LiteLLM or OpenAI.
- Secrets never leave the bank's proxy. The repo ships `.env.example` with
  placeholders only.
- Truncated or streaming-cut responses are recoverable — we degrade to a
  default triage instead of 500ing.

**Negative**
- An additional network hop (client → proxy → provider). Latency is higher
  than a direct SDK call. Acceptable because triage is a background-ish
  step, not a user-blocking operation.
- The recovery heuristic for truncated JSON is pragmatic — it will drift if
  the LLM's output schema changes. Covered by a regression test in
  `tests/application/test_triage_ticket_use_case.py`.
