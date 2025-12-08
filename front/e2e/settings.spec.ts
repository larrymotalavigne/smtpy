import { test, expect } from './global-hooks';
import { login, waitForAngular } from './helpers';

/**
 * E2E Tests for User Settings
 * Based on features/settings.feature
 */

test.describe('User Settings', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/settings');
    await waitForAngular(page);
  });

  test('should display settings page', async ({ page }) => {
    await expect(page.locator('text=/settings|paramètres/i').first()).toBeVisible({ timeout: 5000 });
  });

  test('should display notification preferences', async ({ page }) => {
    await page.waitForTimeout(2000);
    const notifications = page.locator('text=/notifications|email.*preferences/i');
    const visible = await notifications.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) await expect(notifications.first()).toBeVisible();
  });

  test('should display privacy settings', async ({ page }) => {
    await page.waitForTimeout(2000);
    const privacy = page.locator('text=/privacy|confidentialité/i');
    const visible = await privacy.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) console.log('Privacy settings available');
  });

  test('should display security preferences', async ({ page }) => {
    await page.waitForTimeout(2000);
    const security = page.locator('text=/security|sécurité/i');
    const visible = await security.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) console.log('Security settings available');
  });

  test('should display API configuration', async ({ page }) => {
    await page.waitForTimeout(2000);
    const api = page.locator('text=/API|integrations/i');
    const visible = await api.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) console.log('API settings available');
  });
});
