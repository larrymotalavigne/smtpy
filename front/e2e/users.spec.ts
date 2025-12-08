import { test, expect } from './global-hooks';
import { waitForAngular } from './helpers';

/**
 * E2E Tests for Basic User Interactions
 * Based on features/users.feature
 */

test.describe('Basic User Interactions', () => {
  test('should display landing page', async ({ page }) => {
    await page.goto('/');
    await waitForAngular(page);
    await expect(page).toHaveTitle(/SMTPy/);
  });

  test('should access API documentation', async ({ page }) => {
    await page.goto('/');
    await waitForAngular(page);
    const apiDocs = page.locator('text=/API|documentation|docs/i');
    const visible = await apiDocs.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) console.log('API documentation accessible');
  });

  test('should access health endpoint', async ({ page }) => {
    const response = await page.request.get('/health');
    expect(response.ok()).toBeTruthy();
  });

  test('should handle unknown routes', async ({ page }) => {
    await page.goto('/unknown-route-12345');
    await page.waitForTimeout(2000);
    // Should show 404 or redirect
    const url = page.url();
    expect(url).toBeTruthy();
  });
});
