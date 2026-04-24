# Architecture Decision Records

Each ADR captures one architectural choice, the context that forced it, and
the consequences — positive and negative — we accepted by making it.
Superseded decisions stay in the list with status `Superseded by ADR N`.

| # | Title | Status |
| --- | --- | --- |
| [0001](./0001-clean-architecture.md) | Clean Architecture with Domain / Application / Infrastructure / Interfaces | Accepted |
| [0002](./0002-litellm-for-triage.md) | LiteLLM proxy for AI-assisted triage | Accepted |
| [0003](./0003-test-pyramid.md) | Three-layer test pyramid (unit / integration / E2E) | Accepted |

## Writing a new ADR

1. Copy an existing file to `NNNN-short-kebab-title.md`.
2. Keep it short — a reader should grasp the trade-off in under two minutes.
3. Link it from this index.
