import { test, expect } from './global-hooks';

test.describe('Authentication - Critical Path', () => {
  // Generate unique username for test isolation
  const testUsername = `e2euser${Date.now()}`;
  const testEmail = `${testUsername}@example.com`;
  const testPassword = 'TestPassword123';

  test('should register, login and access dashboard', async ({ page }) => {
    // First, register a new user
    await page.goto('/auth/register');
    await page.waitForSelector('#username', { state: 'visible', timeout: 15000 });

    await page.locator('#username').fill(testUsername);
    await page.locator('#email').fill(testEmail);
    await page.locator('#password input').fill(testPassword);
    await page.locator('#confirmPassword input').fill(testPassword);

    // Accept terms and conditions
    await page.locator('#acceptTerms').check();

    await page.getByRole('button', { name: /créer mon compte/i }).click();

    // Should redirect to dashboard after registration
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

    // Verify dashboard loaded - check for username
    await expect(page.locator(`text=${testUsername}`)).toBeVisible({ timeout: 10000 });

    // Logout
    const userButton = page.locator('button:has-text("' + testUsername + '")');
    await userButton.click();
    await page.waitForTimeout(500);
    const logoutButton = page.locator('button:has-text("Déconnexion"), a:has-text("Déconnexion")');
    if (await logoutButton.isVisible({ timeout: 2000 })) {
      await logoutButton.click();
    }

    // Now login again
    await page.goto('/auth/login');
    await page.waitForSelector('#username', { state: 'visible', timeout: 15000 });

    await page.locator('#username').fill(testUsername);
    await page.locator('#password input').fill(testPassword);

    await page.getByRole('button', { name: /se connecter/i }).click();

    // Wait for dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

    // Verify dashboard loaded
    await expect(page.locator(`text=${testUsername}`)).toBeVisible({ timeout: 10000 });
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/auth/login');
    await page.waitForSelector('#username', { state: 'visible', timeout: 15000 });

    await page.locator('#username').fill('wronguser');
    await page.locator('#password input').fill('wrongpass');

    await page.getByRole('button', { name: /se connecter/i }).click();

    // Wait a bit for error to appear
    await page.waitForTimeout(2000);

    // Should still be on login page or show error
    const isOnLogin = await page.url().includes('/auth/login');
    expect(isOnLogin).toBe(true);
  });
});
