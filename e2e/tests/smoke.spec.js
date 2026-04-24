import { test, expect } from '@playwright/test'

// ---------- API contract smoke ----------

test.describe('API contract', () => {
  test('health endpoint returns ok', async ({ request }) => {
    const apiBase = process.env.E2E_API_BASE_URL || `http://127.0.0.1:${process.env.E2E_API_PORT || '8001'}`
    const response = await request.get(`${apiBase}/health`)
    expect(response.ok()).toBeTruthy()
  })

  test('OpenAPI spec is served and documents tickets routes', async ({ request }) => {
    const apiBase = process.env.E2E_API_BASE_URL || `http://127.0.0.1:${process.env.E2E_API_PORT || '8001'}`
    const response = await request.get(`${apiBase}/openapi.json`)
    expect(response.ok()).toBeTruthy()
    const spec = await response.json()
    expect(spec.openapi).toMatch(/^3\./)
    expect(spec.paths).toBeTruthy()
    // The tickets router exposes these core paths:
    expect(spec.paths).toHaveProperty('/tickets/workbench')
    expect(spec.paths).toHaveProperty('/tickets/analytics')
  })

  test('ticket workbench list responds with JSON', async ({ request }) => {
    const apiBase = process.env.E2E_API_BASE_URL || `http://127.0.0.1:${process.env.E2E_API_PORT || '8001'}`
    const response = await request.get(`${apiBase}/tickets/workbench`)
    expect(response.ok()).toBeTruthy()
    const payload = await response.json()
    expect(payload).toHaveProperty('items')
    expect(Array.isArray(payload.items)).toBe(true)
  })
})

// ---------- UI smoke ----------

test.describe('Web UI', () => {
  test('landing page loads and shows navigation to the dashboard', async ({ page }) => {
    await page.goto('/')
    // The app's sidebar lists navigation labels in German.
    await expect(page.getByRole('link', { name: 'Übersicht' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Alle Tickets' })).toBeVisible()
  })

  test('navigating to the tickets page shows a tickets heading or empty state', async ({ page }) => {
    await page.goto('/tickets')
    // Be tolerant: either the tickets table or the empty-state placeholder should appear.
    await expect(page.locator('body')).toContainText(/Ticket|Keine/i)
  })
})
