# E2E Tests (Playwright)

End-to-end smoke tests that spin up the FastAPI backend and the Vite dev server,
then drive them with Chromium via Playwright.

## Run locally

```bash
# 1. Make sure the backend dependencies are installed in the repo root
pip install -r ../requirements.txt

# 2. Install Playwright and its browsers
npm install
npm run install-browsers

# 3. Run the suite
npm test
```

Playwright starts both servers itself via the `webServer` config in
`playwright.config.js` — you do not have to launch them manually.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `E2E_API_PORT` | `8001` | Port the test backend listens on |
| `E2E_WEB_PORT` | `5175` | Port the test Vite dev server listens on |

The backend runs against a disposable SQLite file (`e2e_triage.db`) so tests never
touch your real database. The file is gitignored.

LLM calls are not made during E2E tests; only deterministic endpoints are exercised.
