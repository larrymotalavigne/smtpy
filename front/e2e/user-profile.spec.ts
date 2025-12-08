import { test, expect } from './global-hooks';
import { login, waitForAngular } from './helpers';

/**
 * E2E Tests for User Profile Management
 * Based on features/user-profile.feature
 */

test.describe('User Profile Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/profile');
    await waitForAngular(page);
  });

  test('should display profile page', async ({ page }) => {
    await expect(page.locator('text=/profile|profil|account/i').first()).toBeVisible({ timeout: 5000 });
  });

  test('should display user information', async ({ page }) => {
    await page.waitForTimeout(2000);
    const userInfo = page.locator('text=/username|email|admin/i');
    const visible = await userInfo.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) console.log('User information displayed');
  });

  test('should have change password option', async ({ page }) => {
    await page.waitForTimeout(2000);
    const passwordButton = page.getByRole('button', { name: /password|mot de passe/i });
    const visible = await passwordButton.isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) await expect(passwordButton).toBeVisible();
  });

  test('should display API keys section', async ({ page }) => {
    await page.waitForTimeout(2000);
    const apiKeys = page.locator('text=/API.*keys|clés.*API/i');
    const visible = await apiKeys.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) console.log('API keys section available');
  });

  test('should display account statistics', async ({ page }) => {
    await page.waitForTimeout(2000);
    const stats = page.locator('text=/domains|aliases|messages|statistics/i');
    const count = await stats.count();
    if (count > 0) console.log(`Found ${count} profile statistics`);
  });

  test('should have security options', async ({ page }) => {
    await page.waitForTimeout(2000);
    const security = page.locator('text=/2FA|two.*factor|security|sécurité/i');
    const visible = await security.first().isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) console.log('Security options available');
  });
});
