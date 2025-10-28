import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for SMTPy E2E tests
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: !process.env.CI,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 3,
  reporter: process.env.CI ? [['html'], ['github']] : 'html',
  timeout: 30000,

  use: {
    baseURL: 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Note: Web server is managed externally (via Docker Compose)
  // For local development, run: docker compose -f docker-compose.dev.yml up -d
  // For CI, the workflow starts services before running tests
});
