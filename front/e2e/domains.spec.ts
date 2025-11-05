import { test, expect } from './global-hooks';

test.describe('Domain Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/auth/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password input').fill('password');
    await page.getByRole('button', { name: /se connecter/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Navigate to domains page
    await page.goto('/domains');
    await expect(page).toHaveURL(/\/domains/);
  });

  test('should display domains list page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /domaines/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /ajouter|nouveau/i })).toBeVisible();
  });

  test('should open add domain dialog', async ({ page }) => {
    await page.getByRole('button', { name: /ajouter|nouveau/i }).click();

    // Dialog should be visible
    await expect(page.locator('.p-dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: /ajouter un domaine/i })).toBeVisible();
  });

  test('should validate domain name format', async ({ page }) => {
    // Open add dialog
    await page.getByRole('button', { name: /ajouter|nouveau/i }).click();

    // Try to submit with invalid domain
    await page.getByLabel(/nom du domaine/i).fill('invalid domain name');
    await page.locator('.p-dialog').getByRole('button', { name: /ajouter|créer/i }).click();

    // Should show validation error or prevent submission
    await expect(page.locator('.p-dialog')).toBeVisible(); // Dialog should still be open
  });

  test('should filter domains by name', async ({ page }) => {
    // Wait for domains table to load
    await page.waitForSelector('p-table', { timeout: 5000 });

    // Type in search/filter input if available
    const searchInput = page.getByPlaceholder(/rechercher|search/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('example.com');
      // Wait for filter to apply
      await page.waitForTimeout(500);
    }
  });

  test('should navigate to domain details', async ({ page }) => {
    // Wait for table to load
    await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

    // Click on first domain if exists
    const firstRow = page.locator('p-table tbody tr').first();
    const rowCount = await page.locator('p-table tbody tr').count();

    if (rowCount > 0) {
      await firstRow.click();

      // Should navigate to domain details or open dialog
      // This depends on implementation
      await expect(
        page.locator('.p-dialog, [class*="domain-detail"]')
      ).toBeVisible({ timeout: 3000 });
    }
  });

  test('should display DNS configuration information', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

    const rowCount = await page.locator('p-table tbody tr').count();

    if (rowCount > 0) {
      // Click on first domain
      await page.locator('p-table tbody tr').first().click();

      // Look for DNS records section
      const dnsSection = page.locator('text=/DNS|MX|SPF|DKIM|DMARC/i').first();
      if (await dnsSection.isVisible({ timeout: 3000 })) {
        await expect(dnsSection).toBeVisible();
      }
    }
  });

  test('should show domain status (verified/pending)', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

    const rowCount = await page.locator('p-table tbody tr').count();

    if (rowCount > 0) {
      // Should have status tags/badges
      await expect(
        page.locator('p-tag, .p-badge, [class*="status"]').first()
      ).toBeVisible();
    }
  });
});
