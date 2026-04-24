# ADR 0003: Three-layer test pyramid (unit / integration / E2E)

- **Status:** Accepted
- **Date:** 2026-04-24
- **Decision makers:** Core team

## Context

The codebase has to satisfy three separate confidence budgets:

1. **Correctness of business rules** (priority escalation, SLA computation,
   category normalization). Fast feedback wanted, lots of cases.
2. **Correctness of integrations** (FastAPI route wiring, SQLAlchemy
   persistence, JSON schemas). Medium speed, real I/O against SQLite.
3. **Correctness of user journeys** (operator creates a ticket → sees AI
   recommendation → accepts → assigns → closes). Slow, but irreplaceable.

TDD cannot work if all three live in the same suite — either everything is
slow and nobody runs it, or the slow bits get skipped and regressions slip
through.

## Decision

We split tests along the layering of ADR 0001:

| Layer | Directory | Runner | What it tests | Typical runtime |
| --- | --- | --- | --- | --- |
| **Unit** | `tests/unit/`, `tests/application/` | pytest | Domain rules, use cases with in-memory repositories, pure helpers. No HTTP, no DB driver. | < 1 s per file |
| **Integration** | `tests/api/` | pytest + `TestClient` | FastAPI routes end-to-end against a real SQLite DB. Middleware, serialization, auth wiring all exercised. | 1–5 s per file |
| **E2E** | `e2e/tests/` | Playwright (Chromium) | Full stack: FastAPI + Vite + browser. Disposable SQLite file, placeholder LLM credentials. | 20–60 s per suite |

- Unit + integration run **on every push/PR** as two parallel CI jobs.
- E2E runs **after** backend + frontend jobs, so it only burns compute when
  the cheaper layers are green.
- A 75 % backend coverage floor is enforced via `--cov-fail-under=75` in
  `pyproject.toml`. Frontend coverage is reported but not gated — the UI is
  validated primarily through Playwright.

## Consequences

**Positive**
- TDD loop for business logic stays in the 3–4 s range.
- Integration tests catch route-wiring bugs (status codes, JSON shape)
  without needing a browser.
- E2E guards the handful of flows that have to keep working for the demo
  and the presentation.

**Negative**
- Three different runners, three sets of config. New contributors have to
  learn where their test belongs. Mitigated by directory naming and the
  README's testing section.
- Playwright is occasionally flaky in CI (network, port contention). We
  accept the cost because UI regressions are otherwise invisible.
