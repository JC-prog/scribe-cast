import { defineConfig, devices } from '@playwright/test'

// Assumes the app is already running — either `npm run dev` (against a
// locally running backend) or the full `docker compose up` stack — at
// E2E_BASE_URL. Not wired into `npm run build`/CI: it needs live
// redis+api+worker containers (and a real model download on first run),
// which is a different commitment than a fast unit-test suite.
export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
