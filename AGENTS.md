# AGENTS.md — Agent- und Tool-Dokumentation

Dieses Dokument beschreibt, welche KI-/Coding-Agenten in diesem Projekt zum Einsatz kommen,
welche Tools und Prompts genutzt werden, und nach welchen Spezifikationen neue Funktionalität
hinzugefügt wird.

Es ersetzt nicht die [`README.md`](./README.md) (Setup, Nutzung), sondern ergänzt sie um den
Blickwinkel *„Wie wird hier mit Agenten gearbeitet?“*.

---

## 1. Projekt-Spezifikation (Spec-first)

**Use Case**: Ticket-Triage für den Bank-IT-Support. Jedes neue Ticket soll durch einen
KI-Agenten kategorisiert, priorisiert und einem passenden Team vorgeschlagen werden, bevor
ein menschlicher Operator es final freigibt.

**Architektur-Kontrakt** (verbindlich für alle Änderungen):

| Schicht | Verantwortung | Darf abhängen von |
|---|---|---|
| `app/domain` | Entitäten, Enums, Regeln, Domänenkonstanten | — (keine Framework-Imports) |
| `app/application` | Use Cases, DTOs, Ports | `domain` |
| `app/infrastructure` | SQLAlchemy, LiteLLM, scikit-learn, Settings | `domain`, `application` |
| `app/interfaces` | FastAPI-Router, Schemas, Mapper | alle anderen Schichten |

**Verboten**: Domain oder Application darf weder FastAPI, SQLAlchemy noch LiteLLM direkt
importieren. Die Kommunikation mit der Außenwelt läuft ausschließlich über die Ports in
`app/application/ports/`.

**Entitäten** (mind. 5, siehe `app/domain/entities/`):
`Ticket`, `TicketEvent`, `Assignment`, `TriageAnalysis`, `TriageDecision`, `SimilarCase`.

**Use-Case-Services** (siehe `app/application/use_cases/`): `create_ticket`, `triage_ticket`,
`save_triage_decision`, `assign_ticket`, `update_ticket_status`, `escalate_ticket`,
`add_ticket_comment`, `list_tickets`, `get_ticket`, `get_dashboard_analytics`,
`retrain_model`, `review_triage_decision`.

**Ports** (siehe `app/application/ports/`): `ClassifierPort`, `TicketRepositoryPort`,
`SimilarTicketsPort`.

---

## 2. Eingesetzte Agenten

### 2.1 Laufzeit-Agent: LiteLLM Classifier

- **Code**: `app/infrastructure/ai/litellm_classifier.py`
- **Modell (Default)**: `azure_ai/gpt-oss-120b` via LiteLLM-Proxy
- **Zweck**: Klassifiziert ein neues Ticket nach `category`, `priority`, `suggested_team`,
  `suggested_department`, liefert `summary`, `next_step`, `rationale` auf Deutsch.
- **Port**: `app.application.ports.classifier_port.ClassifierPort`
- **Robustheit**: `_recover_partial_json()` rekonstruiert verkürzte Antworten per Regex,
  damit die Pipeline nicht bei abgeschnittenen Completions kippt.
- **Konfiguration** (ENV):
  - `LITELLM_API_BASE` – Endpoint des LiteLLM-Proxys
  - `LITELLM_API_KEY` – Proxy-Key
  - `LITELLM_MODEL` – Modell-Bezeichner
- **Fallbacks**: Bei fehlendem Proxy/Key greift die Anwendung auf `MLClassifier`
  (scikit-learn, TF-IDF + Multinomial Naive Bayes) bzw. `BaselineClassifier`
  (reine Heuristik) zurück — alle implementieren denselben `ClassifierPort`.

**System-Prompt (verdichtet)**:

```
You are an expert ticket routing assistant for an IT support organization in a banking system.
Analyze the ticket title and description and provide a single JSON response.
Fields: category, priority, suggested_team, suggested_department, summary, next_step, rationale.
Allowed categories: bug, feature, support, requirement, question, unknown.
Allowed priorities: low, medium, high, critical.
suggested_department must be one of the known banking-IT departments.
Default route: suggested_team = "it-support-team" unless escalation is required.
summary, next_step, rationale in German, each ≤ 1 short sentence.
Return valid JSON only.
```

Der vollständige Prompt samt User-Message steht in `litellm_classifier.py::analyze()`.

### 2.2 Retrieval-Agent: RagAssistedClassifier

- **Code**: `app/infrastructure/ai/rag_assisted_classifier.py` (Decorator)
  plus `app/infrastructure/ai/tfidf_similar_tickets.py` (Retrieval-Adapter)
- **Zweck**: Reichert jede LLM-Antwort mit den drei ähnlichsten, von Operatoren
  bereits reviewten Tickets an. Der LLM bekommt diese Fälle als zusätzlichen
  System-Kontext, die UI zeigt sie als klickbare Referenzen im Preview-Popup.
- **Port**: `app.application.ports.similar_tickets_port.SimilarTicketsPort`
- **Technik**: scikit-learn `TfidfVectorizer(ngram_range=(1, 2))` + cosine
  `NearestNeighbors`. Der Index wird beim App-Start aus der Datenbank aufgebaut
  (Filter: `reviewed_by IS NOT NULL`) und lebt als Singleton in `app.state`.
- **Rebuild**: `POST /admin/rebuild-rag` oder Neustart.
- **Cold Start**: Unter `MIN_CORPUS_SIZE=3` reviewten Tickets liefert der Adapter
  leer zurück; der Decorator delegiert dann an den LLM ohne RAG-Kontext.
- **Fehlertoleranz**: Retrieval-Fehler werden im Decorator abgefangen — die
  Triage-Pipeline fällt auf plain-LLM-Klassifikation zurück statt zu kippen.
- **ADR**: [docs/adr/0004-retrieval-augmented-triage.md](./docs/adr/0004-retrieval-augmented-triage.md)
  erklärt die Entscheidung und die verworfenen Alternativen (embeddings,
  pgvector, Tool-using Agent).

### 2.3 Trainings-Agent: scikit-learn Pipeline

- **Code**: `app/infrastructure/ai/train_model.py`
- **Input**: `data/issues.csv` (Spalten `title`, `body`, `label`)
- **Output**: `app/infrastructure/ai/models/triage_model.pkl` (TF-IDF + Multinomial NB)
- **Use Case**: `app/application/use_cases/retrain_model.py`, Endpoint `POST /admin/retrain`

### 2.4 Coding-Agent: Claude (Cowork / Claude Code)

Für Implementierungsarbeit, Refactorings und Tests wird ein KI-Coding-Agent aktiv genutzt.
Leitplanken:

- Jede Änderung respektiert den Architekturkontrakt aus §1.
- Neue Use Cases werden zuerst als Test (`tests/application/…`) skizziert
  (TDD — Red/Green/Refactor), dann implementiert.
- Änderungen an API-Schemata werden immer gespiegelt in
  `app/interfaces/api/schemas/` und den Mappers in `app/interfaces/api/mappers/`.
- Commit-Messages folgen der Konvention `type: description`
  (z. B. `refactor: …`, `feat: …`, `fix: …`), siehe `git log`.

---

## 3. Tool-Inventar

| Bereich | Tool / Library | Datei / Ort |
|---|---|---|
| API-Framework | FastAPI | `app/interfaces/api/app.py` |
| ORM | SQLAlchemy | `app/infrastructure/persistence/` |
| Datenbank | SQLite (lokal), PostgreSQL (Render) | `render.yaml`, `app/infrastructure/persistence/db.py` |
| LLM-Gateway | LiteLLM / OpenAI-SDK | `app/infrastructure/ai/litellm_classifier.py` |
| Klassisches ML | scikit-learn, joblib | `app/infrastructure/ai/ml_classifier.py`, `train_model.py` |
| Retrieval (RAG) | scikit-learn `TfidfVectorizer` + `NearestNeighbors` | `app/infrastructure/ai/tfidf_similar_tickets.py`, `rag_assisted_classifier.py` |
| Frontend | React 19 + Vite + React Router + Axios + Recharts | `frontend/` |
| Tests Backend | pytest, FastAPI `TestClient` | `tests/` |
| Tests Frontend | Vitest + @testing-library/react | `frontend/src/**/*.test.jsx` |
| Tests E2E | Playwright | `e2e/` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |
| Release | GitHub Actions → GHCR | `.github/workflows/release.yml` |
| CD | GitHub Actions → Render Deploy Hooks | `.github/workflows/cd.yml` |
| Container | Docker (multi-stage) | `Dockerfile`, `.dockerignore` |
| Cloud | Render (Web Service + Static Site + Postgres) | `render.yaml` |

---

## 4. Environment / Secrets

| Variable | Wo gesetzt | Zweck |
|---|---|---|
| `LITELLM_API_BASE` | `.env` lokal, Render Env / GitHub Secret | LLM-Proxy-Endpoint |
| `LITELLM_API_KEY` | `.env` lokal, Render Env / GitHub Secret | LLM-Proxy-Key |
| `LITELLM_MODEL` | `render.yaml` / Default | Modell-Bezeichner |
| `DATABASE_URL` | Render bindet PostgreSQL an / `.env` lokal | ORM-Connection-String |
| `CORS_ALLOW_ORIGIN_REGEX` | `render.yaml` | Erlaubte Frontend-Origins |
| `VITE_API_BASE_URL` | Render Static Site / Build-Arg | Backend-Base-URL des Frontends |
| `RENDER_DEPLOY_HOOK_API` | GitHub Secret | CD triggert Backend-Redeploy |
| `RENDER_DEPLOY_HOOK_FRONTEND` | GitHub Secret | CD triggert Frontend-Redeploy |

`.env` ist in `.gitignore` und darf **nie** committed werden.

---

## 5. Workflow: Neue Funktionalität hinzufügen

Empfohlener Ablauf (TDD-basiert):

1. **Spec** formulieren (1–3 Sätze): Was tut der Use Case, welche Entitäten/Ports
   benötigt er?
2. **Test schreiben** unter `tests/application/` (und ggf. `tests/api/` für den
   HTTP-Kontrakt). Der Test muss zuerst rot sein.
3. **Port** anlegen oder erweitern in `app/application/ports/`, falls externe
   Abhängigkeiten nötig sind.
4. **Use Case** implementieren in `app/application/use_cases/`.
5. **Infrastruktur-Adapter** implementieren bzw. erweitern.
6. **API-Route + Schema + Mapper** verdrahten in `app/interfaces/api/`.
7. **Frontend** erweitern (`frontend/src/interfaces/...`) und gegen die API testen.
8. **CHANGES.md / README.md** aktualisieren, wenn das nutzerrelevant ist.
9. **PR eröffnen** → CI muss grün sein (pytest + Vitest + Playwright + Build).

---

## 6. Qualitätskriterien

- **Coverage**: Backend-Tests decken Domain-Regeln, Use Cases und API-Contracts ab.
  Coverage-Report wird als CI-Artefakt abgelegt (`coverage.xml`).
- **Kein Mocking der Domain**: Unit-Tests auf Domain-Ebene arbeiten mit echten
  Entitäten, nicht mit Mocks.
- **API-Schemas via Pydantic**: Jede Response ist ein explizites Schema, damit die
  OpenAPI-Spezifikation unter `/docs` / `/openapi.json` aussagekräftig bleibt.
- **Determinismus der Tests**: LLM-Calls werden in Tests via `monkeypatch` gegen
  `litellm.completion` ersetzt (siehe `tests/api/test_litellm_triage_endpoint.py`).

---

## 7. Bekannte Grenzen & Backlog

- LLM-Proxy muss extern erreichbar sein — ohne gültigen `LITELLM_API_KEY` fällt die
  Triage auf `MLClassifier` zurück.
- Das lokale SQLite-File wird im Container nicht persistiert; für Produktion ist
  PostgreSQL erforderlich (in `render.yaml` bereits verdrahtet).
- Frontend ist deutschsprachig auf Bank-IT-Support zugeschnitten — Mehrsprachigkeit
  ist bewusst nicht im Scope.
