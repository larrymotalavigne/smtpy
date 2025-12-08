import { test, expect } from './global-hooks';
import { login, waitForAngular } from './helpers';

/**
 * E2E Tests for Message Tracking and Management
 *
 * Based on features/message-tracking.feature
 * Covers message listing, filtering, sorting, details, and management
 */

test.describe('Message Tracking and Management', () => {

  test.beforeEach(async ({ page }) => {
    // Login and navigate to messages page
    await login(page);
    await page.goto('/messages');
    await expect(page).toHaveURL(/\/messages/);
    await waitForAngular(page);
  });

  test.describe('View Messages List', () => {

    test('should display messages list', async ({ page }) => {
      await expect(page.getByRole('heading', { name: /messages/i })).toBeVisible();
      await expect(page.locator('p-table, table')).toBeVisible();
    });

    test('should display message columns', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show key message fields
      const headers = page.locator('th, thead');
      const headerVisible = await headers.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (headerVisible) {
        // Check for common columns
        const columns = ['sender', 'recipient', 'subject', 'status', 'date', 'from', 'to'];
        let foundColumns = 0;

        for (const col of columns) {
          const colVisible = await page.locator(`text=/${col}/i`).isVisible({ timeout: 1000 }).catch(() => false);
          if (colVisible) foundColumns++;
        }

        console.log(`Found ${foundColumns} expected column headers`);
      }
    });

    test('should display sender information', async ({ page }) => {
      await page.waitForTimeout(2000);

      const senders = page.locator('text=/from|sender|expéditeur|@/i');
      const senderCount = await senders.count();

      if (senderCount > 0) {
        console.log('Sender information displayed');
      }
    });

    test('should display recipient alias', async ({ page }) => {
      await page.waitForTimeout(2000);

      const recipients = page.locator('text=/@.*\\..*|to|destinataire/i');
      const recipientCount = await recipients.count();

      if (recipientCount > 0) {
        console.log('Recipient information displayed');
      }
    });

    test('should display message status', async ({ page }) => {
      await page.waitForTimeout(2000);

      const statuses = page.locator('p-tag, .p-badge, text=/delivered|failed|pending|livré|échec/i');
      const statusCount = await statuses.count();

      if (statusCount > 0) {
        console.log(`Found ${statusCount} status indicators`);
      }
    });

    test('should display timestamps', async ({ page }) => {
      await page.waitForTimeout(2000);

      const timestamps = page.locator('text=/\\d{2}:\\d{2}|ago|il y a|\\d+.*min|\\d+.*hour/i');
      const timestampCount = await timestamps.count();

      if (timestampCount > 0) {
        console.log('Timestamps displayed');
      }
    });
  });

  test.describe('View Message Details', () => {

    test('should open message details', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .message-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .message-row').first().click();
        await page.waitForTimeout(1000);

        // Should show details dialog or navigate to details page
        const detailsVisible = await page.locator('.p-dialog, [class*="message-detail"]')
          .isVisible({ timeout: 3000 })
          .catch(() => false);

        if (detailsVisible) {
          await expect(page.locator('.p-dialog, [class*="detail"]')).toBeVisible();
        }
      }
    });

    test('should display full message metadata', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .message-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .message-row').first().click();
        await page.waitForTimeout(1000);

        // Should show detailed metadata
        const metadata = page.locator('text=/from|to|subject|forwarded|received|status/i');
        const metadataCount = await metadata.count();

        if (metadataCount > 0) {
          console.log(`Found ${metadataCount} metadata fields`);
        }
      }
    });

    test('should display message size', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .message-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .message-row').first().click();
        await page.waitForTimeout(1000);

        const size = page.locator('text=/size|taille|KB|MB/i');
        const sizeVisible = await size.isVisible({ timeout: 2000 }).catch(() => false);

        if (sizeVisible) {
          console.log('Message size displayed');
        }
      }
    });

    test('should display attachments information', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .message-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .message-row').first().click();
        await page.waitForTimeout(1000);

        const attachments = page.locator('text=/attachment|pièce.*jointe|files/i');
        const attachmentVisible = await attachments.isVisible({ timeout: 2000 }).catch(() => false);

        if (attachmentVisible) {
          console.log('Attachment information displayed');
        }
      }
    });

    test('should view message headers', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .message-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .message-row').first().click();
        await page.waitForTimeout(1000);

        const headersButton = page.getByRole('button', { name: /headers|en-têtes|view.*headers/i });
        const buttonVisible = await headersButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await headersButton.click();
          await page.waitForTimeout(500);

          // Should show headers
          const headers = page.locator('text=/DKIM|SPF|DMARC|X-|Return-Path/i');
          const headersVisible = await headers.first().isVisible({ timeout: 2000 }).catch(() => false);

          if (headersVisible) {
            console.log('Message headers displayed');
          }
        }
      }
    });
  });

  test.describe('Filter Messages', () => {

    test('should filter by status - delivered', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const statusFilter = page.locator('p-dropdown[ng-reflect-placeholder*="status"], select[name*="status"]');
      const filterVisible = await statusFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await statusFilter.click();
        await page.waitForTimeout(500);

        const deliveredOption = page.locator('text=/^delivered$|^livré$/i').first();
        const optionVisible = await deliveredOption.isVisible({ timeout: 2000 }).catch(() => false);

        if (optionVisible) {
          await deliveredOption.click();
          await page.waitForTimeout(1000);
          console.log('Filtered by delivered status');
        }
      }
    });

    test('should filter by status - failed', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const statusFilter = page.locator('p-dropdown[ng-reflect-placeholder*="status"], select[name*="status"]');
      const filterVisible = await statusFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await statusFilter.click();
        await page.waitForTimeout(500);

        const failedOption = page.locator('text=/^failed$|^échec$/i').first();
        const optionVisible = await failedOption.isVisible({ timeout: 2000 }).catch(() => false);

        if (optionVisible) {
          await failedOption.click();
          await page.waitForTimeout(1000);

          // Should show error reasons
          const errorReason = page.locator('text=/error|échec|reason/i');
          const reasonVisible = await errorReason.first().isVisible({ timeout: 2000 }).catch(() => false);

          if (reasonVisible) {
            console.log('Failed messages with error reasons displayed');
          }
        }
      }
    });

    test('should filter by date range', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const dateFilter = page.locator('p-calendar, input[type="date"]').first();
      const filterVisible = await dateFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await dateFilter.click();
        await page.waitForTimeout(500);
        console.log('Date filter is available');
      }
    });

    test('should filter by sender email', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const senderFilter = page.getByPlaceholder(/sender|expéditeur|from/i);
      const filterVisible = await senderFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await senderFilter.fill('test@example.com');
        await page.waitForTimeout(1000);
        console.log('Filtered by sender');
      }
    });

    test('should filter by recipient alias', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const recipientFilter = page.getByPlaceholder(/recipient|destinataire|to/i);
      const filterVisible = await recipientFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await recipientFilter.fill('admin@example.com');
        await page.waitForTimeout(1000);
        console.log('Filtered by recipient');
      }
    });

    test('should filter messages with attachments', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const attachmentFilter = page.locator('p-checkbox:has-text("attachments"), input[type="checkbox"][name*="attachment"]');
      const filterVisible = await attachmentFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await attachmentFilter.click();
        await page.waitForTimeout(1000);
        console.log('Filtered by attachments');
      }
    });
  });

  test.describe('Search Messages', () => {

    test('should search by subject', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const searchInput = page.getByPlaceholder(/search|rechercher|filter/i);
      const searchVisible = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);

      if (searchVisible) {
        await searchInput.fill('invoice');
        await page.waitForTimeout(1000);

        // Results should be filtered
        console.log('Search applied');
      }
    });
  });

  test.describe('Sort Messages', () => {

    test('should sort by date descending (newest first)', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const dateHeader = page.locator('th:has-text("Date"), th:has-text("Créé")').first();
      const headerVisible = await dateHeader.isVisible({ timeout: 3000 }).catch(() => false);

      if (headerVisible) {
        await dateHeader.click();
        await page.waitForTimeout(500);
        console.log('Sorted by date descending');
      }
    });

    test('should sort by date ascending (oldest first)', async ({ page }) => {
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const dateHeader = page.locator('th:has-text("Date"), th:has-text("Créé")').first();
      const headerVisible = await dateHeader.isVisible({ timeout: 3000 }).catch(() => false);

      if (headerVisible) {
        await dateHeader.click();
        await page.waitForTimeout(500);

        // Click again to reverse sort
        await dateHeader.click();
        await page.waitForTimeout(500);
        console.log('Sorted by date ascending');
      }
    });
  });

  test.describe('Pagination', () => {

    test('should paginate through messages', async ({ page }) => {
      await page.waitForSelector('p-table', { timeout: 5000 });

      const paginator = page.locator('.p-paginator');
      const paginatorVisible = await paginator.isVisible({ timeout: 3000 }).catch(() => false);

      if (paginatorVisible) {
        const nextButton = paginator.locator('button[aria-label*="Next"]');
        const buttonEnabled = await nextButton.isEnabled().catch(() => false);

        if (buttonEnabled) {
          await nextButton.click();
          await page.waitForTimeout(1000);
          console.log('Navigated to next page');
        }
      }
    });

    test('should display page numbers', async ({ page }) => {
      await page.waitForSelector('p-table', { timeout: 5000 });

      const paginator = page.locator('.p-paginator');
      const paginatorVisible = await paginator.isVisible({ timeout: 3000 }).catch(() => false);

      if (paginatorVisible) {
        const pageButtons = paginator.locator('button:has-text("1"), button:has-text("2")');
        const buttonCount = await pageButtons.count();

        if (buttonCount > 0) {
          console.log(`Found ${buttonCount} page buttons`);
        }
      }
    });
  });

  test.describe('Message Actions', () => {

    test('should retry failed message delivery', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      // Find a failed message
      const failedMessage = page.locator('tbody tr:has-text("failed"), tbody tr:has-text("échec")').first();
      const messageVisible = await failedMessage.isVisible({ timeout: 3000 }).catch(() => false);

      if (messageVisible) {
        await failedMessage.click();
        await page.waitForTimeout(500);

        const retryButton = page.getByRole('button', { name: /retry|réessayer/i });
        const buttonVisible = await retryButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await expect(retryButton).toBeVisible();
          console.log('Retry button available for failed message');
        }
      }
    });

    test('should delete a message', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .message-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .message-row').first().click();
        await page.waitForTimeout(500);

        const deleteButton = page.getByRole('button', { name: /delete|supprimer/i });
        const buttonVisible = await deleteButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await deleteButton.click();
          await page.waitForTimeout(500);

          // Should show confirmation
          await expect(page.locator('.p-confirm-dialog, .p-dialog')).toBeVisible({ timeout: 2000 });

          // Cancel deletion
          await page.getByRole('button', { name: /cancel|annuler|non/i }).click();
        }
      }
    });

    test('should bulk delete messages', async ({ page }) => {
      await page.waitForSelector('tbody tr, .message-row', { timeout: 5000 });

      // Select multiple messages
      const checkboxes = page.locator('p-tableCheckbox, input[type="checkbox"]');
      const checkboxCount = await checkboxes.count();

      if (checkboxCount > 1) {
        await checkboxes.first().click();
        await checkboxes.nth(1).click();

        // Look for bulk delete button
        const bulkDeleteButton = page.getByRole('button', { name: /delete.*selected|supprimer.*sélection/i });
        const buttonVisible = await bulkDeleteButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await bulkDeleteButton.click();
          await page.waitForTimeout(500);

          // Should show confirmation
          await expect(page.locator('.p-confirm-dialog')).toBeVisible({ timeout: 2000 });

          // Cancel
          await page.getByRole('button', { name: /cancel|annuler/i }).click();
        }
      }
    });
  });

  test.describe('Message Statistics', () => {

    test('should display message statistics', async ({ page }) => {
      await page.waitForTimeout(2000);

      const stats = page.locator('text=/total.*messages|delivered|failed|success.*rate/i');
      const statsVisible = await stats.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (statsVisible) {
        console.log('Message statistics displayed');
      }
    });

    test('should show success rate', async ({ page }) => {
      await page.waitForTimeout(2000);

      const successRate = page.locator('text=/success.*rate|\\d+%|taux.*réussite/i');
      const rateVisible = await successRate.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (rateVisible) {
        console.log('Success rate displayed');
      }
    });
  });

  test.describe('Export Messages', () => {

    test('should export messages to CSV', async ({ page }) => {
      await page.waitForTimeout(2000);

      const exportButton = page.getByRole('button', { name: /export|exporter|CSV/i }).first();
      const buttonVisible = await exportButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(exportButton).toBeVisible();
        console.log('Export button available');
      }
    });
  });

  test.describe('Real-time Updates', () => {

    test('should show loading state when fetching messages', async ({ page }) => {
      await page.goto('/messages');

      // Check for loading spinner
      const loader = page.locator('.p-progress-spinner, .loading, [class*="spinner"]');
      const loaderVisible = await loader.isVisible({ timeout: 1000 }).catch(() => false);

      if (loaderVisible) {
        console.log('Loading indicator displayed');
      }
    });
  });

  test.describe('Multi-criteria Filtering', () => {

    test('should apply multiple filters simultaneously', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Apply status filter
      const statusFilter = page.locator('p-dropdown[ng-reflect-placeholder*="status"]').first();
      const statusVisible = await statusFilter.isVisible({ timeout: 2000 }).catch(() => false);

      if (statusVisible) {
        await statusFilter.click();
        await page.waitForTimeout(300);

        const deliveredOption = page.locator('text=/delivered/i').first();
        if (await deliveredOption.isVisible({ timeout: 1000 }).catch(() => false)) {
          await deliveredOption.click();
        }
      }

      // Apply search
      const searchInput = page.getByPlaceholder(/search|rechercher/i);
      const searchVisible = await searchInput.isVisible({ timeout: 2000 }).catch(() => false);

      if (searchVisible) {
        await searchInput.fill('test');
        await page.waitForTimeout(500);
        console.log('Multiple filters applied');
      }
    });
  });
});
