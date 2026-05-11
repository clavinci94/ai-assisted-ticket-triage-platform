# AGENTS.md

Operational guide for AI coding agents (Claude Code, Cursor, Codex, GitHub Copilot, etc.) working on this repository.

> If you are an AI assistant reading this: **follow the hard rules below verbatim.** When in doubt, ask the human user before destroying state. The README is for humans; this file is for you.

---

## The codebase in 60 seconds

This is a **ticket triage platform** that pairs an LLM with a TF-IDF retrieval layer over human-confirmed past decisions, plus a **YAML-driven Knowledge-Engineering prioritizer** that scores every incoming ticket on four operational dimensions (Wichtigkeit, Dringlichkeit, Aufwand, Lösbarkeit).

| What | Stack | Where |
|---|---|---|
| Backend | FastAPI 0.x, SQLAlchemy, Pydantic v2, Python 3.11 | `app/` |
| Frontend | React 19, Vite, React Router, Axios, Recharts | `frontend/` |
| AI | scikit-learn (TF-IDF + Naive Bayes), LiteLLM (OpenAI-compatible) | `app/infrastructure/ai/` |
| Persistence | SQLite (dev), Postgres (prod) | `app/infrastructure/persistence/` |
| Policy | YAML rules + Python adapter | `app/infrastructure/triage_policy.yaml` |
| Tests | pytest (75% gate), Vitest, Playwright | `tests/`, `frontend/src/`, `e2e/` |
| CI/CD | GitHub Actions → Render | `.github/workflows/` |

The default DB in dev is `sqlite:///./triage.db` (or `dev.db` if `DATABASE_URL` is set in `.env`). Render uses Postgres via `DATABASE_URL`.

---

## Hard rules

Non-negotiable. Violating these creates real bugs (some have already happened — that's why they're rules).

1. **Hexagonal architecture is enforced.** Dependency arrows point *inward only.*
   - `app/domain` — pure Python, **no** framework imports (no `fastapi`, no `sqlalchemy`, no `litellm`, no `pydantic`).
   - `app/application` — depends only on `domain`. Defines ports (abstract interfaces), use cases, DTOs.
   - `app/infrastructure` — implements ports. Imports from `domain` + `application`. Owns SQLAlchemy, LiteLLM, scikit-learn, YAML.
   - `app/interfaces` — FastAPI routes, Pydantic schemas, mappers. Top of the stack, can import from anywhere.

2. **All external dependencies cross a port.** If a use case needs the LLM, similar tickets, prioritization, or persistence, it depends on a port in `app/application/ports/`, not on a concrete adapter. New external integrations get a new port.

3. **Tests must not pollute the demo database.** `tests/conftest.py` sets `DATABASE_URL` to a tmp SQLite file *before* any `app.*` import. Never remove or weaken this — a previous regression leaked `WB-VIEWS-CLAUDIO` test fixtures into the production Render DB. If you add new tests, they inherit isolation automatically.

4. **The RAG corpus is human-confirmed only.** `TfidfSimilarTicketsAdapter._load_reviewed_tickets()` filters on `reviewed_by IS NOT NULL`. Never index tickets that the AI labelled but a human did not endorse — that's the whole point of the design ([ADR 0004](./docs/adr/0004-retrieval-augmented-triage.md)).

5. **Seed prefixes are reserved.** Ticket IDs starting with `DEMO-` or `HIST-` belong to the seeded corpus (`app/infrastructure/seeding/demo_tickets.py`). Never create non-seed tickets with these prefixes; never delete seeded tickets except via `seed(replace=True)`.

6. **Postgres enforces foreign keys; SQLite doesn't.** When deleting tickets, always delete `ticket_events` first. There's a helper for this: `_delete_tickets()` in the seeder. A direct `DELETE FROM tickets WHERE …` will succeed on SQLite and fail on Postgres with `ForeignKeyViolation`. Use the helper.

7. **`ensure_ticket_columns()` is the migration system.** No Alembic. To add a column to `tickets`: (a) add it to `TicketRecordModel` in `app/infrastructure/persistence/models.py` and (b) add a corresponding `_ensure_ticket_column(...)` call in `ensure_ticket_columns()` in `app/infrastructure/persistence/db.py`. The function runs on every app start; idempotent. Don't break this — it's the only thing that keeps Postgres in sync after a deploy.

8. **Never commit `.env`, `.claude/`, `*.db`, or secrets.** `.gitignore` already covers these; verify before `git add`. `git status` before every commit.

9. **Don't add documentation files unless asked.** No README.md / CHANGELOG.md / SECURITY.md unless the user explicitly requests it. Inline comments only when the *why* is non-obvious.

10. **Format and lint before committing.** Run `ruff format app tests` and `ruff check app tests` until both are clean. CI will reject formatting-only failures.

---

## Critical commands

Exact incantations. Use these verbatim.

### Backend

```bash
# activate venv (one-time per shell)
source .venv/bin/activate

# run all tests
python -m pytest tests/ -q

# run with coverage gate (must be ≥ 75%)
python -m pytest --cov=app --cov-fail-under=75

# format + lint (both must pass before commit)
ruff format app tests
ruff check app tests

# security scan
bandit -r app -c pyproject.toml

# start dev server (auto-reload on .py changes)
uvicorn app.main:app --reload

# seed demo + historical corpus (DEMO-*, HIST-*)
python scripts/seed_demo_tickets.py --replace
```

### Frontend

```bash
cd frontend
npm install                  # one-time
npm run dev                  # vite at :5173
npm test -- --run            # vitest
npm run lint                 # eslint
npm run build                # production bundle (dist/)
```

### End-to-end (Playwright)

```bash
cd e2e
npm install                  # one-time
npm run install-browsers     # one-time
npm test
```

### Combined dev

```bash
./dev.sh                     # backend on :8000 + frontend on :5173
```

### Render operations (production, idempotent)

```bash
# clean + reseed demo corpus and rebuild RAG index
curl -X POST https://ai-assisted-ticket-triage-api.onrender.com/admin/seed-demo

# fill prioritization for legacy tickets
curl -X POST https://ai-assisted-ticket-triage-api.onrender.com/admin/backfill-prioritization
```

---

## Code style

Defaults that the rest of the codebase follows. New code matches these without exception.

### Python

- **Type hints everywhere.** Function signatures, dataclass fields, port methods. `from __future__ import annotations` is fine.
- **Dataclasses for domain entities**, Pydantic for HTTP schemas. Never the other way around.
- **No docstrings on simple functions.** Module-level docstrings explaining *why* are OK; per-function docstrings only when behaviour is genuinely surprising.
- **No comments that restate the code.** No `# loop over tickets`. Only comments that capture a *why* a reader couldn't reconstruct from the code itself — hidden invariants, performance trade-offs, links to incidents.
- **Imports are absolute** (`from app.domain.entities.ticket import Ticket`), never relative.
- **Names of ports end in `Port`**, adapters end in `Adapter` or descriptive (`PolicyBasedPrioritizer`, `MLClassifier`).
- **No `print()`.** Use the configured logger. JSON-line output is set up in `app/infrastructure/logging/`.
- **Pydantic v2 syntax**: `model_config = ConfigDict(...)`, not the v1 `Config` class.

### TypeScript / JSX

- **No TypeScript yet** — the frontend is plain JavaScript with JSX. Don't introduce `.ts` / `.tsx` files; this project intentionally stays JS-only.
- **Functional components only.** No class components.
- **State that survives reloads goes in `localStorage`** via `loadStoredJson` / `persistJson` (see `frontend/src/application/tickets/ticketWorkbench.js`). Always include a forward-merge step when adding new defaults so returning users get them (see the column-visibility migration in `TicketsPage.jsx`).
- **Recharts only.** Don't introduce another chart library.

### Commit messages

Conventional Commits, lowercase type. Examples from `git log`:

```
feat(seeding): enrich RAG corpus with 60 historical tickets + clean seeder
fix(workbench): forward-merge new default columns for returning users
style(seeding): apply ruff format to demo_tickets
docs: explain knowledge-engineered prioritization in README
chore: prune unused assets and refresh README structure
test(e2e): align smoke test with post-IA sidebar
```

Body wrapped at ~72 cols, explains the *why* not the *what*. Use a HEREDOC to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
type(scope): short summary

Why this exists, what it changes, references to issues / ADRs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Architecture contract

```
domain        ← pure Python, no framework imports
  ↑
application   ← use cases, ports, DTOs. depends on domain only
  ↑
infrastructure ← adapters: SQLAlchemy, LiteLLM, scikit-learn, YAML
  ↑
interfaces    ← FastAPI routes, Pydantic schemas, mappers
```

### Ports (verify these exist before adding new external integrations)

| Port | Location | Implementations |
|---|---|---|
| `ClassifierPort` | `app/application/ports/classifier_port.py` | `MLClassifier`, `LitellmClassifier`, `RagAssistedClassifier`, `BaselineClassifier` |
| `SimilarTicketsPort` | `app/application/ports/similar_tickets_port.py` | `TfidfSimilarTicketsAdapter` |
| `PrioritizationPort` | `app/application/ports/prioritization_port.py` | `PolicyBasedPrioritizer` |
| `TicketRepositoryPort` | `app/application/ports/ticket_repository_port.py` | `SQLiteTicketRepository` (also serves Postgres) |

### Use cases

Coordinator objects. They take ports in `__init__` and orchestrate a single business operation in `execute()`. See `app/application/use_cases/`:

```
add_ticket_comment, assign_ticket, backfill_prioritization,
create_ticket, escalate_ticket, get_dashboard_analytics, get_ticket,
list_tickets, retrain_model, review_triage_decision,
save_triage_decision, triage_ticket, update_ticket_status
```

Don't add business logic to FastAPI route handlers. Route handlers wire DI, call a use case, map the result to a Pydantic schema.

---

## Domain knowledge an agent will need

Things that aren't obvious from reading the code.

### Knowledge-engineered prioritization (KE layer)

Every ticket gets four scores plus two derived signals — computed by `PolicyBasedPrioritizer` after the classifier runs:

| Field | Range | Source |
|---|---|---|
| `impact_score` | 1–5 | YAML rule match (`app/infrastructure/triage_policy.yaml`) |
| `urgency_score` | 1–5 | YAML rule match |
| `effort_estimate_minutes` | int | mean of `effort_estimate_minutes` across top-k RAG neighbours; YAML fallback (`default_effort_minutes`) when no neighbours |
| `solvability` | `self-service` / `l1` / `l2` / `specialist` | YAML rule match |
| `composite_priority` | 1–25 | derived: `impact × urgency`, sorts the workbench |
| `auto_resolve_eligible` | bool | derived: `solvability == self-service` ∧ `category_confidence ≥ self_service_confidence_threshold` ∧ `runbook_url is not None` |

The YAML is the source of truth. Editing rules ≠ code change. The file format is:

```yaml
self_service_confidence_threshold: 0.6
default_effort_minutes: 60
rules:
  - id: <slug>
    match: { tags_any: [...], department: "...", title_any: [...], ai_category_any: [...], ai_priority_any: [...] }
    set: { impact_score: int, urgency_score: int, solvability: str, runbook_url: str, rationale: str }
default: { impact_score: int, urgency_score: int, solvability: str, rationale: str }
```

Rules are evaluated in order; later matches override earlier values per field. First matched `runbook_url` wins.

### Seed corpus structure

- `DEMO-001..DEMO-020` — 20 curated showcase tickets across 6 departments. Defined in `DEMO_TICKETS` list, `app/infrastructure/seeding/demo_tickets.py`. Use for the live demo.
- `HIST-001..HIST-060` — 60 historical tickets across 8 thematic clusters (VPN/Citrix, password/lockout, hardware, SAP, payments, mobile/online banking, compliance, retail/corporate/lending). Defined in `HISTORICAL_TICKETS`. Use to give the RAG layer meaningful neighbours for every common scenario.
- `_DEFAULT_EFFORT_BY_TAG` maps the dominant tag of each seed to a baseline effort in minutes. The seeder also runs the prioritizer over every seed at insert time, so DEMO/HIST rows arrive in the DB with full `impact_score` / `urgency_score` / `solvability` / etc.
- `TEST_POLLUTION_TITLE_PREFIXES` is the kill-list for known pytest fixtures (`WB-PAGE-CLAUDIO*`, `Workflow * Test`, …). The seeder's `purge_test_pollution=True` (default on) removes them.

### Database migrations

There is no Alembic. Schema changes propagate via `ensure_ticket_columns()` in `app/infrastructure/persistence/db.py`. It runs `ALTER TABLE tickets ADD COLUMN ...` for every column not yet present. To add a column:

1. Add it to `TicketRecordModel` in `models.py` (SQLAlchemy declaration).
2. Add a `_ensure_ticket_column("col_name", "col_name TYPE …")` line to `ensure_ticket_columns()`.

The function is idempotent and runs on every app start. Don't change this approach to Alembic without a migration plan that handles existing production data.

### Test database isolation

`tests/conftest.py` sets `os.environ["DATABASE_URL"]` to a tmp SQLite file *before* any `app.*` import — because `app/infrastructure/persistence/db.py` reads `DATABASE_URL` at import time and the engine is global. Don't:

- Move the `os.environ` set below an `app.*` import (it won't apply)
- Remove the `pytest_sessionfinish` cleanup unless you want every CI run to leave a tmp dir
- Use the production engine in tests

To inspect the test DB after a failed run: `KEEP_TEST_DB=1 pytest tests/...`.

### Frontend localStorage migrations

Workbench column visibility is persisted in `localStorage["ticket-workbench-columns"]`. When you add a column to `DEFAULT_VISIBLE_COLUMNS`, the loader in `TicketsPage.jsx` forward-merges missing keys so returning users see the new column. Don't bypass this — every new default column must reach existing users.

### Render auto-deploy

The CD workflow (`.github/workflows/cd.yml`) only fires the Render deploy hook **after CI passes** on `main`. So a `git push` triggers: CI run → on success → CD hits the API deploy hook + frontend deploy hook → Render rebuilds. Free-tier rebuild takes 3–5 minutes. The deploy hook secrets are `RENDER_DEPLOY_HOOK_API` and `RENDER_DEPLOY_HOOK_FRONTEND` in GitHub repo secrets.

After a deploy that adds new columns or seed structure, the human user usually wants you to also call the admin endpoints (`seed-demo`, `backfill-prioritization`) once over HTTP to refresh the production data — these are idempotent and safe to call repeatedly.

---

## Workflow for new features

Mirror what the rest of the codebase does. The recipe:

1. **Confirm scope** with the user if the change is non-trivial (touching multiple layers, a port, or visible UI).
2. **Spec the contract** — one paragraph: input/output shapes, which port(s) involved, which entities.
3. **Write the test first** in `tests/application/` (for use cases) or `tests/api/` (for HTTP contract) or `tests/unit/` (for pure functions). Confirm it fails.
4. **Domain entities** in `app/domain/entities/` if new shapes are needed. Pure dataclasses, no framework imports.
5. **Port** in `app/application/ports/` if an external dependency is involved. Abstract base class, abstract method, docstring explaining the contract.
6. **Use case** in `app/application/use_cases/`. Constructor takes ports, `execute(...)` returns a result DTO.
7. **Adapter** in `app/infrastructure/` implementing the port.
8. **Route + Pydantic schema + mapper** in `app/interfaces/api/`. The route is a thin wrapper around the use case.
9. **Frontend** in `frontend/src/interfaces/...`. Update `api.js` if it's a new endpoint, add the component, wire localStorage migration if relevant.
10. **Run the full pipeline locally**: `python -m pytest tests/ -q && ruff format app tests && ruff check app tests && cd frontend && npm test -- --run && npm run build`.
11. **Commit** with a conventional-commits message (see Code style). Don't `git add -A` blindly; check `git status` first.
12. **Push** only when the user authorizes it. Do not push to `main` without explicit consent for the current change.

---

## Testing

- **Coverage gate is 75%.** Falls below = CI red.
- **Unit tests** (`tests/unit/`) exercise pure logic: policy rules, similarity scoring, priority rules, schema migration. No DB, no app fixtures.
- **Application tests** (`tests/application/`) exercise use cases against fakes / minimal repos. No HTTP.
- **API tests** (`tests/api/`) drive the HTTP surface via FastAPI's `TestClient`. They share the isolated tmp DB.
- **LLM is mocked** in API tests via `monkeypatch` against `litellm.completion`. See `tests/api/test_litellm_triage_endpoint.py` for the pattern. Don't make real LLM calls in tests.
- **E2E** (`e2e/`, Playwright) drives the full UI against a real backend + frontend. Slow; run before shipping UI changes.

When you add a new port + adapter, write:
- 1 unit test for the adapter (deterministic inputs)
- 1 application test that the use case calls the port correctly
- 1 API test if the port is observable through HTTP

---

## Common pitfalls

Real bugs that have happened. Don't repeat them.

| Pitfall | Why it bit | The fix |
|---|---|---|
| `SEED_PREFIX = "00"` while seed IDs were `"1"..."20"` | `--replace` flag did nothing for months | Use unambiguous prefixes (`DEMO-`, `HIST-`); test against the actual id pattern |
| `DELETE FROM tickets WHERE …` without deleting `ticket_events` first | Worked on SQLite, exploded on Postgres FK constraint | Use `_delete_tickets()` helper which deletes events first |
| Pytest writing to `triage.db` because no `DATABASE_URL` isolation | 200+ test-fixture rows leaked into production | `conftest.py` sets `DATABASE_URL` to tmp file before any `app.*` import |
| Frontend column added to `DEFAULT_VISIBLE_COLUMNS` but returning users had stored old list | New column invisible until localStorage cleared | Forward-merge: append missing default keys to the stored list on load |
| `_to_analysis_response()` called without prioritization in the `/triage` mapper | Workbench cells empty even when DB had data | Pass `result.prioritization` through to the analysis response too, not just the top-level field |
| Committing `.claude/scheduled_tasks.lock` | Agent state in repo | Added `.claude/` to `.gitignore`; verify `git status --short` before commit |
| Running `--no-verify` on a hook failure | Commits the broken state | Fix the root cause (usually ruff format), re-stage, new commit. Never bypass hooks unless the user explicitly asks. |
| Adding a docstring to every function "for documentation" | Code review noise, fights project style | No docstrings on simple functions — only module-level *why* docs and per-function docs where behaviour is surprising |

---

## When to ask vs. proceed

**Proceed without asking:**
- Local-only changes that don't touch shared state (editing code, running tests, formatting)
- Reversible operations with low blast radius (creating files, editing files)
- Following an existing established pattern

**Ask the human first:**
- Destructive operations: `git reset --hard`, `git push --force`, `rm -rf`, dropping DB tables
- Force-pushing to `main`
- Calling production admin endpoints (`/admin/seed-demo`, `/admin/backfill-prioritization`) for the first time in a session
- Operations that send to third parties (Slack, email, PR posts, comments on GitHub issues)
- Changes that span more than 5 files or refactor a port's contract
- Anything where you'd otherwise have to guess what the user wants

**Default: confirm if unsure.** The cost of pausing is low; the cost of an unwanted destructive action is high.

---

## Files an agent should read first

When the user gives you a task that touches one of these areas, read the corresponding file *before* writing any code:

| Task | Read first |
|---|---|
| Anything touching triage | `app/application/use_cases/triage_ticket.py` |
| Anything touching the RAG | `app/infrastructure/ai/tfidf_similar_tickets.py` + `rag_assisted_classifier.py` |
| Anything touching prioritization | `app/infrastructure/triage_policy.yaml` + `app/infrastructure/ai/policy_based_prioritizer.py` + `app/domain/entities/prioritization.py` |
| Adding a column to tickets | `app/infrastructure/persistence/models.py` + `db.py` (`ensure_ticket_columns`) |
| Adding a workbench column | `frontend/src/application/tickets/ticketWorkbench.js` + `frontend/src/interfaces/components/TicketList.jsx` + `frontend/src/interfaces/pages/TicketsPage.jsx` (for the localStorage migration) |
| Reports/analytics changes | `app/application/use_cases/get_dashboard_analytics.py` + `frontend/src/interfaces/pages/ReportsPage.jsx` |
| Seed corpus changes | `app/infrastructure/seeding/demo_tickets.py` |
| New port | `app/application/ports/classifier_port.py` (canonical example) |
| CI/CD changes | `.github/workflows/ci.yml` + `cd.yml` + `release.yml` |
| Architecture decisions | `docs/adr/` (numbered ADRs in chronological order) |

---

## ADR pointers

| ADR | What it decides |
|---|---|
| [0001](./docs/adr/0001-record-architecture-decisions.md) | We use ADRs |
| [0002](./docs/adr/0002-hexagonal-architecture.md) | Hexagonal layering and the dependency-arrow rule |
| [0003](./docs/adr/0003-litellm-as-llm-gateway.md) | LiteLLM as the single LLM gateway (avoid lock-in) |
| [0004](./docs/adr/0004-retrieval-augmented-triage.md) | RAG with TF-IDF over reviewed tickets; rejected sentence-transformers / pgvector / agent loops |

When you make a non-obvious architectural choice, write an ADR rather than burying the rationale in a commit message.

---

## Summary for impatient agents

1. Hexagonal arrows point inward. Domain has no framework imports.
2. RAG corpus = reviewed humans only.
3. KE policy lives in `triage_policy.yaml`. Editing rules ≠ code change.
4. Add a column? Both `models.py` *and* `ensure_ticket_columns()` in `db.py`.
5. Delete tickets? Use `_delete_tickets()` — it handles the FK cascade.
6. Test DB is isolated in `conftest.py`. Don't break that.
7. Conventional commits. Format with `ruff format` before commit.
8. Don't push to main without explicit consent for the current change.
9. Ask before calling production admin endpoints or doing anything destructive.
10. When stuck, read the file listed in "Files an agent should read first" before writing code.
