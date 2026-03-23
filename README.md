Hier ist eine **ausführliche, GitHub-konforme `README.md`**, die du direkt per Copy/Paste übernehmen kannst.


# AI-assisted Ticket Triage Platform

An enterprise-style full-stack application for AI-assisted ticket intake, triage, review, assignment, and analytics.

This project was developed as a capstone project for the module **AI-assisted Software Development**. It demonstrates a layered architecture, AI-assisted development workflow, test-driven engineering practices, CI/CD foundations, Docker-based deployment, and a minimal but functional web GUI connected to a REST API.

---

## Project Overview

The **AI-assisted Ticket Triage Platform** supports the intake and processing of tickets in an enterprise-style workflow.

The system combines:
- a **REST API** built with FastAPI,
- a **web frontend** built with React/Vite,
- a **relational database** accessed through SQLAlchemy ORM,
- and an **AI-assisted classification / triage component** to support faster and more consistent ticket routing.

The goal is to reduce manual triage effort, provide a structured review process, and improve transparency through assignment history and analytics.

---

## Core Use Case

The application implements a minimal but meaningful enterprise use case:

> Incoming tickets are created, analyzed by an AI-assisted triage mechanism, reviewed by a human if required, assigned to a responsible team, and tracked through the system.

This reflects a realistic business scenario in IT support, service operations, internal issue processing, or product support workflows.

---

## Key Features

- Create and manage tickets through a REST API
- AI-assisted ticket categorization / triage
- Human review workflow
- Assignment to responsible teams or units
- Ticket history / audit-style tracking
- Minimal analytics and overview capabilities
- Web frontend connected to the API
- OpenAPI / Swagger documentation
- Containerized local execution with Docker
- CI/CD scaffolding for test, release, and deployment workflows

---

## Architecture

This project follows a **layered enterprise-style architecture** to separate business logic from framework and infrastructure concerns.

### Architectural Layers

- **Domain**
  - core entities
  - domain rules
  - business concepts

- **Application**
  - use cases
  - orchestration logic
  - service-level workflows

- **Interfaces**
  - REST API routes
  - request/response mapping
  - dependency wiring

- **Infrastructure**
  - persistence
  - ORM/database access
  - repository implementations
  - external integrations

### Architectural Goals

- separation of concerns
- maintainability
- testability
- clear responsibilities
- reduced coupling between business logic and framework code

---

## Domain Model

The system is centered around several business-relevant entities.  
Depending on the final implementation state, the concrete model may evolve, but the domain currently includes or targets entities such as:

1. **Ticket**
   - the central business object representing an incoming issue/request

2. **Triage Result**
   - AI-assisted classification result, category, or routing suggestion

3. **Review**
   - human validation or correction of the AI-assisted suggestion

4. **Assignment**
   - responsibility assignment to a team, department, or owner

5. **History / Audit Event**
   - traceable changes, actions, or workflow-relevant events over time

These entities support the required business process from intake to handling.

---

## Use Cases / Application Services

The application implements multiple business use cases through dedicated service logic.

### 1. Ticket Intake
A user or system creates a new ticket with relevant metadata and content.

### 2. AI-assisted Triage
The application analyzes ticket content and produces a suggested classification or routing decision.

### 3. Human Review
A reviewer can validate, adjust, or override the AI suggestion.

### 4. Assignment
A ticket is assigned to a responsible team or handling unit.

### 5. Operational Overview / Analytics
The system exposes aggregated views or statistics to support operational insight.

At least two service-oriented use cases are clearly implemented through the application layer, satisfying the capstone requirements.

---

## Technology Stack

### Backend
- **FastAPI**
- **SQLAlchemy**
- **Pydantic**
- **Python**

### Frontend
- **React**
- **Vite**
- **TypeScript / JavaScript** (depending on current frontend implementation)

### AI / Data
- **scikit-learn**
- **pandas**
- **numpy**
- **joblib**

### Database
- **SQLite** for local/simple development fallback
- **PostgreSQL** for containerized / deployment-ready execution

### Tooling / DevOps
- **Docker**
- **Docker Compose**
- **GitHub Actions**
- **Playwright** (E2E scaffolding)

---

## Repository Structure

```text
.
├── app
│   ├── application
│   ├── domain
│   ├── infrastructure
│   └── interfaces
├── frontend
│   ├── src
│   └── tests
├── tests
│   ├── unit
│   ├── application
│   └── api
├── .github
│   └── workflows
├── deploy
├── AGENTS.md
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
└── README.md
````

### Important Directories

* `app/domain`
  Domain entities and business rules

* `app/application`
  Use cases and service orchestration

* `app/interfaces`
  API routes and framework-facing adapters

* `app/infrastructure`
  Database setup, repositories, and persistence layer

* `frontend`
  Web application connected to the backend API

* `tests`
  Backend test suites across multiple levels

* `.github/workflows`
  CI/CD workflows

* `deploy`
  Deployment-related configuration

---

## API

The application is exposed as a **REST API**.

Typical API responsibilities include:

* creating tickets
* retrieving tickets
* updating workflow state
* human review actions
* assignment actions
* health check / system status

### Health Endpoint

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

---

## OpenAPI / Swagger

Because the backend is implemented with FastAPI, OpenAPI documentation is automatically provided.

### Local URLs

* Swagger UI: `http://localhost:8000/docs`
* OpenAPI JSON: `http://localhost:8000/openapi.json`

This satisfies the capstone requirement for an **OpenAPI specification / Swagger documentation**.

---

## Web GUI

The project includes a minimal but functional **web GUI**.

### Goals of the GUI

* provide a simple interface for interacting with the ticket workflow
* consume the REST API
* visualize ticket-related actions and data
* demonstrate frontend-backend integration

The frontend is intentionally lightweight, but fully relevant for the end-to-end flow.

---

## Database & Persistence

The application uses a **relational database** via **SQLAlchemy ORM**.

### Current Setup

* local fallback: SQLite
* containerized / deployment-oriented setup: PostgreSQL

### Persistence Goals

* structured relational data storage
* ORM abstraction through SQLAlchemy
* replaceable runtime configuration through environment variables

### Environment-based DB Configuration

The backend reads `DATABASE_URL` from the environment and falls back to SQLite when the variable is not set.

This allows:

* easy local development
* Docker-based PostgreSQL execution
* future cloud deployment without code changes

---

## Testing Strategy

This project follows a layered testing approach.

### 1. Unit Tests

Focused on isolated logic and small behavioral units.

### 2. Integration Tests

Focused on interactions between API, application logic, and persistence.

### 3. End-to-End Tests

Frontend-oriented E2E test scaffolding is included via Playwright.

### Existing Test Structure

* `tests/unit`
* `tests/application`
* `tests/api`
* `frontend/tests/e2e`

### Test Goal

The goal is not only code coverage, but confidence in:

* business logic correctness
* API behavior
* user-visible flow integrity

### Run Backend Tests

```bash
pytest -q
```

### Run Frontend Build Check

```bash
cd frontend
npm run build
cd ..
```

### Run E2E Tests

```bash
cd frontend
npx playwright test
cd ..
```

---

## AI-assisted Development / Coding Agents

This project was developed with active support from coding agents as required by the module.

The usage policy and working principles are documented in:

```text
AGENTS.md
```

### Coding-agent support included

* scaffolding
* refactoring assistance
* boilerplate generation
* Docker / CI/CD setup
* test support
* documentation drafting

### Human responsibility remained essential for

* architecture decisions
* business logic correctness
* deployment configuration
* code review
* final validation

This reflects a controlled and reviewable AI-assisted engineering workflow.

---

## CI/CD

The repository includes CI/CD scaffolding via **GitHub Actions**.

### CI Workflow

Runs on push / pull request and is intended to validate:

* backend dependencies
* backend tests
* frontend build

### Release Workflow

Intended to:

* build Docker images
* tag artifacts
* publish release assets

### CD Workflow

Prepared as a deployment scaffold and can be connected to a real deployment target such as:

* Render
* Railway
* VPS with Docker Compose

### Workflow Files

```text
.github/workflows/ci.yml
.github/workflows/release.yml
.github/workflows/cd.yml
```

---

## Docker

The project is containerized for reproducible local execution and deployment preparation.

### Available Docker Files

* `Dockerfile.backend`
* `Dockerfile.frontend`
* `docker-compose.yml`

### Services

The Docker setup provides:

* `backend`
* `frontend`
* `db` (PostgreSQL)

### Start with Docker

```bash
docker compose build
docker compose up -d
```

### Check running services

```bash
docker compose ps
```

### Relevant local endpoints

* Backend: `http://localhost:8000`
* Swagger: `http://localhost:8000/docs`
* Frontend: `http://localhost:3000`

### Stop the stack

```bash
docker compose down
```

---

## Local Development

### Backend

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run backend locally:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Default local URLs

* Backend: `http://127.0.0.1:8000`
* Frontend (Vite): `http://127.0.0.1:5173`

---

## Deployment

The project is prepared for container-based deployment.

### Deployment Direction

A cloud deployment can be performed using a platform such as:

* **Render**
* **Railway**
* **VPS with Docker Compose**

### Current Deployment Assets

* Dockerfiles for backend and frontend
* Docker Compose setup
* deployment scaffold in `deploy/`
* environment-variable-based DB configuration

### Recommended Production Direction

* PostgreSQL as production database
* environment-based configuration
* dedicated frontend URL
* backend CORS configured for deployed frontend origin
* real CD pipeline linked to target environment

### Placeholder

Once deployed, add the production URLs here:

* Frontend: `https://<your-frontend-url>`
* Backend: `https://<your-backend-url>`
* Swagger: `https://<your-backend-url>/docs`

---

## Known Limitations / Future Improvements

This project already demonstrates the required capstone capabilities, but several improvements are possible:

* expand E2E coverage beyond smoke tests
* improve bundle splitting and frontend optimization
* replace startup-based table creation with migration tooling
* harden production deployment configuration
* refine repository naming to be database-agnostic
* enhance analytics depth and reporting
* add authentication / authorization if required by future scope

---

## Author / Team

**Project:** AI-assisted Ticket Triage Platform
**Context:** Capstone Project – AI-assisted Enterprise Full-Stack Application

### Team Members

* `Claudio Vinci`
* `Almidin Bangoj`
* `Manuel Pasamontes`


