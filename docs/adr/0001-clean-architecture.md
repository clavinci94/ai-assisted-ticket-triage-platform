# ADR 0001: Clean Architecture with Domain / Application / Infrastructure / Interfaces

- **Status:** Accepted
- **Date:** 2026-04-24
- **Decision makers:** Core team

## Context

The platform has to stay usable for **three independent axes of change**:

1. The business rules (how a ticket gets triaged, what "SLA breached" means,
   which department owns which category) will continue to evolve as the
   bank's support organization matures.
2. The AI backbone is volatile — today it is an Azure-hosted LiteLLM proxy,
   tomorrow it may be a self-hosted model, a classical ML classifier, or a
   hybrid pipeline.
3. The HTTP surface has to stay stable for the React frontend and for any
   future integrations (iPaaS, webhooks, CLI).

If any one of these leaks into the others — for example FastAPI request
objects reaching into business logic, or SQLAlchemy models being returned
from the API — every change becomes expensive.

## Decision

We adopt a **four-layer clean architecture** with a strict, one-way
dependency rule:

```
interfaces  ──►  application  ──►  domain  ◄──  infrastructure
```

| Layer | Contains | May import |
| --- | --- | --- |
| `app/domain` | Entities, enums, constants, pure business rules | stdlib only |
| `app/application` | Use cases, DTOs, ports (abstract interfaces) | `domain` |
| `app/infrastructure` | SQLAlchemy models, LiteLLM/OpenAI clients, config, logging | `domain`, `application` |
| `app/interfaces` | FastAPI routes, Pydantic schemas, DI wiring | all three |

- **Use cases are services** exposing an `execute(...)` method. They orchestrate
  domain objects through **ports** — nothing in the use case knows whether
  the repository is SQLite, Postgres, or in-memory.
- **Entities are framework-free dataclasses.** No Pydantic, no SQLAlchemy.
- **Schemas live in the interfaces layer** and are the only thing FastAPI
  sees; mapping between Pydantic and domain objects is the interfaces layer's
  job (`interfaces/api/mappers/`).

## Consequences

**Positive**
- Swapping SQLite for Postgres on Render was a one-line change: a new
  connection string. Business logic and tests were unaffected.
- Replacing the classical ML classifier with a LiteLLM-backed one is a
  single new infrastructure adapter implementing `ClassifierPort`.
- Use cases are trivial to unit-test — inject a fake repository, call
  `execute()`, assert on the returned DTO. No HTTP, no DB.

**Negative**
- More files up front. A single feature touches at least four layers.
- Mapping boilerplate between Pydantic schemas and domain dataclasses.
  We accept this as the price of framework independence.

## Alternatives considered

- **Transaction Script + flat FastAPI files.** Rejected — rules would scatter
  across routes, and swapping the AI backend would require touching every
  touchpoint.
- **Hexagonal without the "application" layer (routes → domain).** Rejected
  because it conflates HTTP concerns (pagination, query parsing) with
  business orchestration.
