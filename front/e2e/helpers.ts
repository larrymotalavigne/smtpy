import { Page, expect } from '@playwright/test';

/**
 * Helper function to login to the application
 */
export async function login(page: Page, username: string = 'admin', password: string = 'password') {
  await page.goto('/auth/login');

  // Wait for the login form to be fully loaded
  await page.waitForSelector('#username', { state: 'visible', timeout: 10000 });

  // Fill in credentials
  await page.locator('#username').fill(username);
  await page.locator('#password input').fill(password);

  // Submit
  await page.getByRole('button', { name: /se connecter/i }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
}

/**
 * Helper function to logout from the application
 */
export async function logout(page: Page) {
  // Look for logout button - might be in a menu
  const logoutButton = page.locator('button:has-text("Déconnexion"), a:has-text("Déconnexion")');

  if (await logoutButton.isVisible({ timeout: 2000 })) {
    await logoutButton.click();
  } else {
    // Try to open user menu first
    const userMenu = page.locator('[class*="user"], [class*="avatar"], [class*="profile"]').first();
    if (await userMenu.isVisible({ timeout: 2000 })) {
      await userMenu.click();
      await page.waitForTimeout(500);
      await page.locator('button:has-text("Déconnexion"), a:has-text("Déconnexion")').click();
    }
  }

  // Wait for redirect to login
  await expect(page).toHaveURL(/\/auth\/login/, { timeout: 5000 });
}

/**
 * Wait for Angular to be ready
 */
export async function waitForAngular(page: Page) {
  await page.waitForLoadState('networkidle');
  // Additional wait for Angular to bootstrap
  await page.waitForTimeout(1000);
}
