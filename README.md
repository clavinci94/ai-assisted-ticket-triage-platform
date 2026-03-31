# AI-assisted Ticket Triage Platform

A full-stack ticket triage application with a FastAPI backend, a React/Vite frontend, and AI-assisted routing via classic ML and LiteLLM.

The project supports the full workflow from ticket intake to review, assignment, audit trail, and dashboard analytics. The current UI is localized in German and tailored to a banking-style service and support context.

## Features

- Create tickets through a focused dashboard workflow
- Preview an AI recommendation before saving a ticket
- Recommend category, priority, responsible team, and department
- Allow manual department override before persistence
- Review and correct AI decisions
- Assign tickets to teams or owners
- Track history through audit-style events
- Visualize KPIs, ticket status, priorities, and department distribution
- Expose REST endpoints with FastAPI and Swagger/OpenAPI

## Workflow

1. A user creates a ticket in the dashboard.
2. The frontend requests an LLM preview via LiteLLM.
3. The user accepts the suggested department or overrides it manually.
4. The ticket is stored and enriched with AI analysis.
5. Reviewers can confirm or adjust the triage decision.
6. The ticket can then be assigned and tracked through the dashboard.

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- scikit-learn
- LiteLLM

### Frontend

- React
- Vite
- React Router
- Recharts
- Axios

### Persistence

- SQLite (`triage.db`) for local development

## Project Structure

```text
.
├── app
│   ├── application
│   ├── domain
│   ├── infrastructure
│   └── interfaces
├── frontend
│   ├── src
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

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm

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
- Health check: `http://127.0.0.1:8000/health`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- App: `http://127.0.0.1:5173`

The frontend uses `http://127.0.0.1:8000` by default. If needed, you can override it with `VITE_API_BASE_URL`.

## Environment Variables

The current dashboard ticket creation flow uses the LiteLLM-backed endpoints.

Recommended root `.env`:

```env
LITELLM_API_BASE=https://your-litellm-proxy.example.com
LITELLM_API_KEY=sk-your-litellm-virtual-key
LITELLM_MODEL=azure_ai/gpt-oss-120b
```

### Supported Variables

| Variable | Purpose |
| --- | --- |
| `LITELLM_API_BASE` | Base URL of the LiteLLM proxy |
| `LITELLM_API_KEY` | LiteLLM virtual key for proxy access |
| `LITELLM_MODEL` | Model name used for LLM triage |
| `OPENAI_BASE_URL` | Supported alias for LiteLLM proxy base URL |
| `OPENAI_API_KEY` | Supported alias for LiteLLM proxy key |
| `AZURE_API_BASE` | Optional direct Azure AI endpoint |
| `AZURE_API_KEY` | Optional direct Azure AI key |

Notes:

- The preferred setup for this repository is LiteLLM proxy usage.
- Do not commit real keys.
- `litellm_config.yaml` can be used for a local LiteLLM proxy, but it is optional for normal app usage.

## API Overview

### Core Ticket Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/tickets/triage` | Classic ML-based triage |
| `POST` | `/tickets/triage/llm` | Persist ticket using LiteLLM-backed triage |
| `POST` | `/tickets/triage/llm/preview` | Preview AI recommendation without saving |
| `POST` | `/tickets/decision` | Save reviewer decision |
| `POST` | `/tickets/assign` | Assign a ticket |
| `GET` | `/tickets` | List all tickets |
| `GET` | `/tickets/{ticket_id}` | Get ticket details including analysis and history |
| `GET` | `/tickets/analytics` | Dashboard analytics |

### Admin Endpoint

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/admin/retrain` | Retrain the classic ML model |

### System Endpoint

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health check |

## Frontend Pages

The current frontend is split into dedicated views instead of one overloaded dashboard:

- Start page for explanation and platform orientation
- Dashboard overview for daily steering and quick navigation
- Ticket creation page with AI recommendation popup
- KPI dashboard
- Department analysis
- Ticket detail page for review, assignment, and audit trail

## Testing

### Backend Tests

```bash
pytest
```

### Frontend Build Check

```bash
cd frontend
npm run build
```

## Notes

- The local database is created automatically as `triage.db`.
- Schema helper functions add missing department-related columns on startup.
- The frontend creation flow depends on the LiteLLM preview and save endpoints.
- The repository currently contains backend, frontend, and tests only. Older documentation that referenced Docker, PostgreSQL, or GitHub Actions is no longer accurate for the current state of this repo.

## License

No license file is currently included in this repository.
