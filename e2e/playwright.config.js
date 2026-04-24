import { defineConfig, devices } from '@playwright/test'

const API_PORT = process.env.E2E_API_PORT || '8001'
const WEB_PORT = process.env.E2E_WEB_PORT || '5175'
const API_BASE_URL = `http://127.0.0.1:${API_PORT}`
const WEB_BASE_URL = `http://127.0.0.1:${WEB_PORT}`

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: WEB_BASE_URL,
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      // Start the FastAPI backend against a disposable SQLite file.
      command: `python -m uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT}`,
      cwd: '..',
      url: `${API_BASE_URL}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        DATABASE_URL: 'sqlite:///./e2e_triage.db',
        LITELLM_API_BASE: 'http://127.0.0.1:9',
        LITELLM_API_KEY: 'e2e-placeholder',
        LITELLM_MODEL: 'e2e-placeholder',
        CORS_ALLOW_ORIGINS: WEB_BASE_URL,
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${WEB_PORT} --strictPort`,
      cwd: '../frontend',
      url: WEB_BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        VITE_API_BASE_URL: API_BASE_URL,
      },
    },
  ],
})
