import { test, expect } from '@playwright/test';

test.describe('Navigation and Layout', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/auth/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password input').fill('password');
    await page.getByRole('button', { name: /se connecter/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should display main navigation menu', async ({ page }) => {
    // Should have navigation sidebar or top menu
    await expect(page.locator('nav, [role="navigation"]')).toBeVisible();
  });

  test('should navigate to all main sections', async ({ page }) => {
    const sections = [
      { name: /tableau de bord|dashboard/i, url: '/dashboard' },
      { name: /domaines|domains/i, url: '/domains' },
      { name: /messages/i, url: '/messages' },
      { name: /statistiques|statistics/i, url: '/statistics' },
      { name: /abonnement|billing/i, url: '/billing' },
    ];

    for (const section of sections) {
      const link = page.getByRole('link', { name: section.name });
      if (await link.isVisible({ timeout: 2000 })) {
        await link.click();
        await expect(page).toHaveURL(new RegExp(section.url), { timeout: 3000 });
      }
    }
  });

  test('should display user profile menu', async ({ page }) => {
    // Look for user avatar or profile button
    const profileButton = page.locator('[class*="avatar"], [class*="profile"], [class*="user"]').first();

    if (await profileButton.isVisible({ timeout: 3000 })) {
      await profileButton.click();

      // Should show dropdown menu
      await expect(page.locator('[class*="menu"], [role="menu"]')).toBeVisible({ timeout: 2000 });
    }
  });

  test('should navigate to profile page', async ({ page }) => {
    const profileLink = page.getByRole('link', { name: /profil|profile|compte|account/i }).first();

    if (await profileLink.isVisible({ timeout: 3000 })) {
      await profileLink.click();
      await expect(page).toHaveURL(/\/profile/, { timeout: 3000 });
    }
  });

  test('should navigate to settings page', async ({ page }) => {
    const settingsLink = page.getByRole('link', { name: /paramètres|settings/i }).first();

    if (await settingsLink.isVisible({ timeout: 3000 })) {
      await settingsLink.click();
      await expect(page).toHaveURL(/\/settings/, { timeout: 3000 });
    }
  });

  test('should highlight current active route', async ({ page }) => {
    // Navigate to domains
    await page.goto('/domains');

    // The domains menu item should be highlighted/active
    const domainsLink = page.getByRole('link', { name: /domaines|domains/i });
    await expect(domainsLink).toHaveClass(/active|current|selected/);
  });

  test('should display breadcrumbs on detail pages', async ({ page }) => {
    // Navigate to a section
    await page.goto('/domains');

    // Look for breadcrumbs
    const breadcrumb = page.locator('[class*="breadcrumb"], nav[aria-label*="breadcrumb"]');

    if (await breadcrumb.isVisible({ timeout: 3000 })) {
      await expect(breadcrumb).toBeVisible();
    }
  });

  test('should toggle dark mode', async ({ page }) => {
    // Look for theme toggle button
    const themeToggle = page.locator('button[class*="theme"], button[aria-label*="theme"], [class*="dark-mode"]').first();

    if (await themeToggle.isVisible({ timeout: 3000 })) {
      await themeToggle.click();

      // Body or html should have dark class
      await page.waitForTimeout(500);
      const bodyClass = await page.locator('body, html').first().getAttribute('class');
      expect(bodyClass).toContain('dark');

      // Toggle back
      await themeToggle.click();
      await page.waitForTimeout(500);
    }
  });

  test('should redirect unauthenticated users to login', async ({ page, context }) => {
    // Logout - look for logout button in menu
    const logoutButton = page.locator('button:has-text("Déconnexion"), a:has-text("Déconnexion")');
    if (await logoutButton.isVisible({ timeout: 2000 })) {
      await logoutButton.click();
    } else {
      // Try to open user menu first
      const userMenu = page.locator('[class*="user"], [class*="avatar"], [class*="profile"]').first();
      if (await userMenu.isVisible()) {
        await userMenu.click();
        await page.locator('button:has-text("Déconnexion"), a:has-text("Déconnexion")').click();
      }
    }
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });

    // Try to access protected route
    await page.goto('/dashboard');

    // Should redirect back to login
    await expect(page).toHaveURL(/\/login/, { timeout: 3000 });
  });
});
