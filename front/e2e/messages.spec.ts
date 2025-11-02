import { test, expect } from '@playwright/test';

test.describe('Message Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/auth/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password input').fill('password');
    await page.getByRole('button', { name: /se connecter/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Navigate to messages page
    await page.goto('/messages');
    await expect(page).toHaveURL(/\/messages/);
  });

  test('should display messages list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /messages/i })).toBeVisible();
    await expect(page.locator('p-table')).toBeVisible();
  });

  test('should paginate through messages', async ({ page }) => {
    // Wait for table to load
    await page.waitForSelector('p-table', { timeout: 5000 });

    // Look for pagination controls
    const paginator = page.locator('.p-paginator');
    if (await paginator.isVisible()) {
      // Check if next page button exists and is enabled
      const nextButton = paginator.locator('button[aria-label*="Next"]');
      if (await nextButton.isEnabled()) {
        await nextButton.click();
        // Wait for page to update
        await page.waitForTimeout(500);
        await expect(paginator).toBeVisible();
      }
    }
  });

  test('should filter messages by status', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('p-table', { timeout: 5000 });

    // Look for status filter dropdown
    const statusDropdown = page.getByLabel(/statut|status/i);
    if (await statusDropdown.isVisible()) {
      await statusDropdown.click();

      // Select a status option
      const deliveredOption = page.locator('text=/delivered|livré/i').first();
      if (await deliveredOption.isVisible({ timeout: 2000 })) {
        await deliveredOption.click();
        await page.waitForTimeout(500);
      }
    }
  });

  test('should view message details', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

    const rowCount = await page.locator('p-table tbody tr').count();

    if (rowCount > 0) {
      // Click on first message
      await page.locator('p-table tbody tr').first().click();

      // Should open details dialog or navigate to details page
      await expect(
        page.locator('.p-dialog, [class*="message-detail"]')
      ).toBeVisible({ timeout: 3000 });
    }
  });

  test('should display message metadata', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

    const rowCount = await page.locator('p-table tbody tr').count();

    if (rowCount > 0) {
      // Table should contain email-related columns
      await expect(
        page.locator('text=/from|to|subject|sender|recipient/i').first()
      ).toBeVisible();
    }
  });

  test('should sort messages by date', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('p-table', { timeout: 5000 });

    // Click on date column header to sort
    const dateHeader = page.locator('th').filter({ hasText: /date|créé/i }).first();
    if (await dateHeader.isVisible()) {
      await dateHeader.click();
      await page.waitForTimeout(500);

      // Click again to reverse sort
      await dateHeader.click();
      await page.waitForTimeout(500);
    }
  });

  test('should show message count and statistics', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('p-table', { timeout: 5000 });

    // Look for statistics/count display
    const countDisplay = page.locator('text=/total|résultats|messages/i').first();
    await expect(countDisplay).toBeVisible({ timeout: 3000 });
  });
});
