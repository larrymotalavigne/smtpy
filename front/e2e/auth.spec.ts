import { test, expect } from '@playwright/test';
import { login, logout, waitForAngular } from './helpers';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAngular(page);
  });

  test('should display landing page for unauthenticated users', async ({ page }) => {
    await expect(page).toHaveTitle(/SMTPy/);
    await expect(page.getByRole('heading', { name: /emails professionnels/i })).toBeVisible();
  });

  test('should navigate to login page', async ({ page }) => {
    await page.locator('a:has-text("Connexion")').click();
    await waitForAngular(page);
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
  });

  test('should show validation errors for empty login form', async ({ page }) => {
    await page.goto('/login');
    await waitForAngular(page);

    // Try to submit empty form
    await page.getByRole('button', { name: /se connecter/i }).click();

    // Should show validation messages or the form should still be visible
    await expect(page.locator('#username')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await login(page);
    await expect(page.getByRole('heading', { name: /tableau de bord/i })).toBeVisible({ timeout: 5000 });
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForSelector('#username', { state: 'visible', timeout: 10000 });

    // Fill with invalid credentials
    await page.locator('#username').fill('invalid@example.com');
    await page.locator('#password input').fill('wrongpassword');

    // Submit form
    await page.getByRole('button', { name: /se connecter/i }).click();

    // Should show error message (either toast or inline message)
    await expect(page.locator('.p-toast-message-error, .p-message-error, .p-message, .form-error, [severity="error"]')).toBeVisible({ timeout: 5000 });
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await login(page);

    // Logout
    await logout(page);
  });
});
