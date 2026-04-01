# AI-assisted Ticket Triage Platform

Modern ticket triage and operations dashboard for internal support teams. The project combines a FastAPI backend, a React/Vite frontend, AI-assisted ticket classification via LiteLLM, and a banking-style operator UI focused on review, assignment, SLA tracking, and reporting.

The current product state covers the full flow from ticket intake to AI recommendation, manual review, assignment, status handling, audit trail, workbench views, and reporting pages.

## 🔄 Recent Updates (April 2026)

**Commit `882d354`** — *refactor: Improve LLM robustness & enhance dashboard UX*
- **Backend**: LiteLLM Classifier now gracefully recovers from truncated JSON responses via `_recover_partial_json()` method
- **Frontend**: Dashboard hero section now displays operative KPI metrics (Offen/Review/Zuweisung)
- **UI/UX**: Enhanced command-bar grid layout, reduced visual noise, improved responsive styling
- **QA**: All endpoints tested, security verified (API keys in `.env` only, not hardcoded)

See [CHANGES.md](./CHANGES.md) for detailed technical breakdown.

## Highlights

- AI-assisted ticket intake with preview before persistence
- Department recommendation with accept-or-override popup
- Ticket workbench with table views, filters, chips, pagination, and bulk actions
- Ticket detail workflow for review, assignment, status changes, escalation, and comments
- Reporting area for KPIs, departments, teams, SLA monitoring, backlog, and trend charts
- Local settings for operator name and preferred dashboard/reporting start points
- German-localized frontend tailored to internal bank, operations, and support processes

## Product Areas

### Ticket Intake

- Create new tickets from the dashboard
- Generate an AI recommendation before saving
- Show suggested department and rationale in a popup
- Let the user accept the recommendation or override the department manually

### Operational Workbench

- `Alle Tickets`
- `Meine Tickets`
- `Offene Tickets`
- `Eskalationen`
- Search, sorting, multi-filtering, column visibility, pagination, row selection, and bulk actions

### Ticket Workflow

- Review AI triage decisions
- Assign a team and assignee
- Update ticket status
- Escalate high-risk tickets
- Add comments and internal notes
- Maintain an audit-style event timeline

### Reporting & Governance

- Dashboard overview with operational KPI blocks
- KPI reporting page
- Department analysis
- Team report
- SLA / due-date monitoring
- Ticket volume and backlog development charts
- Top assignee and processing-time metrics

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- scikit-learn
- LiteLLM
- python-dotenv

### Frontend

- React
- Vite
- React Router
- Axios
- Recharts

### Persistence

- SQLite for local development (`triage.db`)

## Repository Structure

```text
.
├── app
│   ├── application
│   │   ├── dto
│   │   ├── ports
│   │   └── use_cases
│   ├── domain
│   │   ├── constants
│   │   ├── entities
│   │   ├── enums
│   │   └── rules
│   ├── infrastructure
│   │   ├── ai
│   │   ├── config
│   │   └── persistence
│   └── interfaces
│       └── api
│           ├── mappers
│           ├── routes
│           └── schemas
├── frontend
│   ├── src
│   │   ├── application
│   │   ├── domain
│   │   ├── infrastructure
│   │   └── interfaces
│   └── package.json
├── tests
│   ├── api
│   ├── application
│   └── unit
├── .env.example
├── litellm_config.yaml
├── README.md
├── requirements.txt
└── pytest.ini
```

## Architecture Layers

### Backend

- `domain`: entities, enums, business constants, and domain rules
- `application`: use cases, DTOs, and abstract ports
- `infrastructure`: persistence, AI adapters, configuration, and technical services
- `interfaces`: HTTP routes, schemas, request mapping, and API composition

### Frontend

- `interfaces`: React pages and visual components
- `application`: UI workflows and workbench orchestration
- `domain`: frontend business constants and normalization helpers
- `infrastructure`: HTTP clients and browser storage adapters

## Current Frontend Navigation

- `Startseite`: explanation, usage guidance, and platform overview
- `Übersicht`: operator dashboard with KPI summaries and action areas
- `Alle Tickets`: central workbench table
- `Meine Tickets`: tickets assigned to the configured operator
- `Offene Tickets`: active open queue
- `Eskalationen`: high-priority and escalated tickets
- `Ticket erfassen`: ticket creation with AI preview popup
- `Reports`: reporting hub
- `KPIs`
- `Abteilungen`
- `Teams`
- `SLA / Fristen`
- `Einstellungen`

## API Overview

### Ticket Triage & Workflow

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/tickets/triage` | Classic ML-based triage |
| `POST` | `/tickets/triage/llm` | Persist ticket with LiteLLM-backed triage |
| `POST` | `/tickets/triage/llm/preview` | Generate AI recommendation without saving |
| `POST` | `/tickets/decision` | Save review decision |
| `POST` | `/tickets/assign` | Assign team and assignee |
| `POST` | `/tickets/status` | Update ticket status |
| `POST` | `/tickets/comments` | Add comment or internal note |
| `POST` | `/tickets/escalate` | Escalate a ticket |

### Ticket Retrieval & Analytics

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/tickets` | Return all ticket records |
| `GET` | `/tickets/workbench` | Filtered and paginated table data |
| `GET` | `/tickets/{ticket_id}` | Ticket details including analysis and events |
| `GET` | `/tickets/analytics` | Dashboard and reporting analytics |

### Other Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/admin/retrain` | Retrain the classic ML model |
| `GET` | `/health` | Service health check |

## Analytics Currently Exposed

The analytics endpoint now provides more than basic status counts. It includes:

- summary stats including total, open, triaged, reviewed, assigned, and closed
- category, priority, status, department, and team distribution
- SLA metrics
- processing time grouped by priority
- top assignees
- ticket volume over time
- backlog development over time

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm

### 1. Backend Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend URLs:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- App: `http://127.0.0.1:5173`

The frontend uses the backend on `http://127.0.0.1:8000` by default. If needed, provide `VITE_API_BASE_URL`.

## Environment Variables

The preferred setup for this repository is LiteLLM proxy usage.

Example `.env`:

```env
LITELLM_API_BASE=https://your-litellm-proxy.example.com
LITELLM_API_KEY=sk-your-litellm-virtual-key
LITELLM_MODEL=azure_ai/gpt-oss-120b
```

### Supported Variables

| Variable | Purpose |
| --- | --- |
| `LITELLM_API_BASE` | LiteLLM proxy base URL |
| `LITELLM_API_KEY` | LiteLLM virtual key |
| `LITELLM_MODEL` | Model name for LLM triage |
| `OPENAI_BASE_URL` | Supported alias for the LiteLLM proxy base URL |
| `OPENAI_API_KEY` | Supported alias for the LiteLLM proxy key |
| `AZURE_API_BASE` | Optional direct Azure AI endpoint |
| `AZURE_API_KEY` | Optional direct Azure AI key |

Notes:

- `.env.example` contains the recommended proxy-based template.
- Do not commit real credentials.
- `litellm_config.yaml` is only needed if you run your own local LiteLLM proxy.

## Development Notes

- The local SQLite database is created automatically as `triage.db`.
- Startup helpers add missing database columns for local schema evolution.
- The UI is currently localized in German.
- The workbench and settings area use local browser storage for operator preferences.
- Existing free-text ticket content is not automatically translated retroactively.

## Testing

### Backend

```bash
pytest
```

### Frontend

```bash
cd frontend
npm run build
```

## License

No license file is currently included in this repository.
