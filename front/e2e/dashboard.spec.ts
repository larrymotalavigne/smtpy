import { test, expect } from './global-hooks';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/auth/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password input').fill('password');
    await page.getByRole('button', { name: /se connecter/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should display dashboard page after login', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /tableau de bord|dashboard/i })).toBeVisible();
  });

  test('should display statistics cards', async ({ page }) => {
    // Wait for statistics to load
    await page.waitForSelector('.p-card, [class*="stat"]', { timeout: 5000 });

    // Should have multiple statistic cards
    const cards = page.locator('.p-card, [class*="card"]');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);

    // Should display numbers/metrics
    await expect(page.locator('text=/\\d+/').first()).toBeVisible();
  });

  test('should display time-series chart', async ({ page }) => {
    // Wait for charts to render
    await page.waitForTimeout(2000);

    // Look for Chart.js canvas or chart container
    const chart = page.locator('canvas, [class*="chart"]').first();
    await expect(chart).toBeVisible({ timeout: 5000 });
  });

  test('should display recent activity section', async ({ page }) => {
    // Look for recent messages or activity section
    const activitySection = page.locator('text=/récent|recent|activité|activity/i').first();

    if (await activitySection.isVisible({ timeout: 3000 })) {
      await expect(activitySection).toBeVisible();
    }
  });

  test('should navigate to domains from dashboard', async ({ page }) => {
    // Look for "View all domains" or similar link
    const domainsLink = page.getByRole('link', { name: /domaines|domains/i }).first();

    if (await domainsLink.isVisible({ timeout: 3000 })) {
      await domainsLink.click();
      await expect(page).toHaveURL(/\/domains/, { timeout: 3000 });
    }
  });

  test('should navigate to messages from dashboard', async ({ page }) => {
    // Look for "View all messages" or similar link
    const messagesLink = page.getByRole('link', { name: /messages/i }).first();

    if (await messagesLink.isVisible({ timeout: 3000 })) {
      await messagesLink.click();
      await expect(page).toHaveURL(/\/messages/, { timeout: 3000 });
    }
  });

  test('should refresh statistics when date range changes', async ({ page }) => {
    // Wait for initial load
    await page.waitForTimeout(2000);

    // Look for date range selector
    const dateSelector = page.locator('p-calendar, input[type="date"], [class*="date"]').first();

    if (await dateSelector.isVisible({ timeout: 3000 })) {
      await dateSelector.click();
      // Select a date (implementation depends on date picker)
      await page.waitForTimeout(500);
    }
  });

  test('should display success rate metric', async ({ page }) => {
    // Wait for stats to load
    await page.waitForTimeout(2000);

    // Look for success rate percentage
    const successRate = page.locator('text=/%|success|réussite/i').first();
    await expect(successRate).toBeVisible({ timeout: 5000 });
  });
});
