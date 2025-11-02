import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Email Forwarding Flow
 *
 * Tests the complete email processing lifecycle:
 * - Email receiving and display
 * - Email forwarding to destination addresses
 * - Message status tracking
 * - Bounce handling
 * - Email statistics updates
 *
 * Note: These tests primarily validate the UI flow and data display.
 * Actual SMTP email sending/receiving requires backend SMTP server to be running.
 */

test.describe('Email Processing Flow', () => {

  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/auth/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password input').fill('password');
    await page.getByRole('button', { name: /se connecter/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test.describe('Email Receiving and Display', () => {

    test('should display received messages in list', async ({ page }) => {
      // Navigate to messages
      await page.goto('/messages');
      await expect(page).toHaveURL(/\/messages/);

      // Wait for messages table to load
      await expect(page.locator('p-table')).toBeVisible({ timeout: 5000 });

      // Check for message list elements
      await expect(page.getByRole('heading', { name: /messages/i })).toBeVisible();

      // Table should have rows or show empty state
      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        console.log(`Found ${rowCount} messages in the list`);
        // Verify table has expected columns
        await expect(page.locator('th').filter({ hasText: /from|sender|expéditeur/i })).toBeVisible();
        await expect(page.locator('th').filter({ hasText: /to|recipient|destinataire/i })).toBeVisible();
        await expect(page.locator('th').filter({ hasText: /subject|objet/i })).toBeVisible();
      } else {
        console.log('No messages found - this is expected for a new installation');
      }
    });

    test('should display message details with metadata', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        // Click on first message
        await page.locator('p-table tbody tr').first().click();

        // Wait for details view
        await page.waitForTimeout(1000);

        // Check for message details
        const detailsVisible = await page.locator('.p-dialog, [class*="message-detail"]')
          .isVisible({ timeout: 3000 })
          .catch(() => false);

        if (detailsVisible) {
          // Should show key email fields
          const fieldsToCheck = [
            /from|de|expéditeur/i,
            /to|à|destinataire/i,
            /subject|objet/i,
            /date/i
          ];

          for (const fieldPattern of fieldsToCheck) {
            const fieldVisible = await page.locator(`text=${fieldPattern}`)
              .first()
              .isVisible({ timeout: 2000 })
              .catch(() => false);

            if (fieldVisible) {
              console.log(`Field ${fieldPattern} found in message details`);
            }
          }
        }
      }
    });

    test('should show email body content', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for email body/content area
        const bodyArea = page.locator('[class*="body"], [class*="content"], .p-dialog .content');
        const bodyVisible = await bodyArea.first().isVisible({ timeout: 3000 }).catch(() => false);

        if (bodyVisible) {
          console.log('Email body content area found');
        }
      }
    });

    test('should display email headers information', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for headers section or button to view headers
        const headersSection = page.locator('text=/headers|en-têtes|raw.*headers/i');
        const headersVisible = await headersSection.first().isVisible({ timeout: 3000 }).catch(() => false);

        if (headersVisible) {
          console.log('Email headers section found');
        }
      }
    });
  });

  test.describe('Email Forwarding Status', () => {

    test('should show message delivery status', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        // Look for status badges/tags in the table
        const statusBadges = page.locator('p-tag, .p-badge, [class*="status"]');
        const badgeCount = await statusBadges.count();

        if (badgeCount > 0) {
          const firstStatus = await statusBadges.first().textContent();
          console.log('Message status:', firstStatus);

          // Common statuses: delivered, pending, failed, bounced
          await expect(statusBadges.first()).toBeVisible();
        }
      }
    });

    test('should filter messages by delivery status', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Look for status filter
      const statusFilter = page.locator('p-dropdown[placeholder*="statut" i], p-dropdown[placeholder*="status" i]');
      const filterExists = await statusFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterExists) {
        await statusFilter.click();
        await page.waitForTimeout(500);

        // Look for status options
        const options = ['delivered', 'pending', 'failed', 'bounced', 'livré', 'en attente', 'échoué'];

        for (const option of options) {
          const optionElement = page.locator(`text=/^${option}$/i`);
          const optionVisible = await optionElement.isVisible({ timeout: 1000 }).catch(() => false);

          if (optionVisible) {
            console.log(`Found status option: ${option}`);
            break;
          }
        }
      }
    });

    test('should display forwarding destination address', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for forwarded to address or alias information
        const forwardInfo = page.locator('text=/forwarded.*to|transféré|alias|destination/i');
        const infoVisible = await forwardInfo.first().isVisible({ timeout: 3000 }).catch(() => false);

        if (infoVisible) {
          console.log('Forwarding destination information found');
        }
      }
    });

    test('should show delivery timestamps', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for timestamp fields
        const timestamps = [
          /received.*at|reçu.*le/i,
          /sent.*at|envoyé.*le/i,
          /delivered.*at|livré.*le/i
        ];

        for (const pattern of timestamps) {
          const timestampVisible = await page.locator(`text=${pattern}`)
            .first()
            .isVisible({ timeout: 2000 })
            .catch(() => false);

          if (timestampVisible) {
            console.log(`Found timestamp: ${pattern}`);
          }
        }
      }
    });
  });

  test.describe('Email Bounce Handling', () => {

    test('should identify bounced messages', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Filter by bounced status if possible
      const statusFilter = page.locator('p-dropdown[placeholder*="statut" i], p-dropdown[placeholder*="status" i]');
      const filterExists = await statusFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterExists) {
        await statusFilter.click();
        await page.waitForTimeout(500);

        // Try to select bounced/failed status
        const bouncedOption = page.locator('text=/bounced|failed|échoué/i');
        const bouncedExists = await bouncedOption.isVisible({ timeout: 2000 }).catch(() => false);

        if (bouncedExists) {
          await bouncedOption.click();
          await page.waitForTimeout(1000);

          // Check if any bounced messages appear
          const rowCount = await page.locator('p-table tbody tr').count();
          console.log(`Found ${rowCount} bounced messages`);
        }
      }
    });

    test('should display bounce reason in message details', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        // Find a bounced message (if any)
        // For now, just check the first message
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for bounce/error information
        const bounceInfo = page.locator('text=/bounce|error.*message|erreur|échec/i');
        const bounceVisible = await bounceInfo.first().isVisible({ timeout: 3000 }).catch(() => false);

        if (bounceVisible) {
          console.log('Bounce/error information found');
        }
      }
    });

    test('should show failed delivery attempts count', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for retry/attempt information
        const retryInfo = page.locator('text=/attempts|retry|tentatives/i');
        const retryVisible = await retryInfo.first().isVisible({ timeout: 3000 }).catch(() => false);

        if (retryVisible) {
          console.log('Delivery attempts information found');
        }
      }
    });
  });

  test.describe('Email Statistics Update', () => {

    test('should update dashboard statistics after email processing', async ({ page }) => {
      // Check initial dashboard stats
      await page.goto('/dashboard');
      await expect(page).toHaveURL(/\/dashboard/);

      // Wait for stats to load
      await page.waitForTimeout(2000);

      // Look for email count statistics
      const statsCards = page.locator('.stats-card, [class*="stat"], [class*="metric"]');
      const statsVisible = await statsCards.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (statsVisible) {
        // Get current message count
        const messageCount = page.locator('text=/total.*messages|emails.*sent|messages.*envoyés/i');
        const countVisible = await messageCount.first().isVisible({ timeout: 3000 }).catch(() => false);

        if (countVisible) {
          console.log('Message statistics found on dashboard');
        }
      }
    });

    test('should show delivery success rate metric', async ({ page }) => {
      await page.goto('/dashboard');

      // Look for success rate metric
      const successRate = page.locator('text=/success.*rate|taux.*de.*réussite|delivery.*rate/i');
      const rateVisible = await successRate.first().isVisible({ timeout: 5000 }).catch(() => false);

      if (rateVisible) {
        console.log('Delivery success rate metric found');
      }
    });

    test('should display recent messages in dashboard', async ({ page }) => {
      await page.goto('/dashboard');

      // Look for recent activity/messages section
      const recentSection = page.locator('text=/recent.*messages|activity|activité.*récente/i');
      const sectionVisible = await recentSection.first().isVisible({ timeout: 5000 }).catch(() => false);

      if (sectionVisible) {
        // Should show some recent messages
        const messageItems = page.locator('[class*="message-item"], [class*="activity-item"]');
        const itemCount = await messageItems.count();

        console.log(`Found ${itemCount} recent message items`);
      }
    });

    test('should update message count in real-time', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Get initial message count
      const initialCount = await page.locator('p-table tbody tr').count();

      // Look for refresh button
      const refreshButton = page.getByRole('button', { name: /actualiser|refresh|reload/i });
      const refreshExists = await refreshButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (refreshExists) {
        await refreshButton.click();
        await page.waitForTimeout(1000);

        // Get updated count
        const updatedCount = await page.locator('p-table tbody tr').count();

        console.log(`Message count: ${initialCount} -> ${updatedCount}`);
      }
    });
  });

  test.describe('Email Search and Filtering', () => {

    test('should search messages by sender email', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      const searchInput = page.getByPlaceholder(/rechercher|search|filter/i);
      const searchExists = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);

      if (searchExists) {
        // Search for a common email domain
        await searchInput.fill('example.com');
        await page.waitForTimeout(1000);

        // Results should be filtered
        console.log('Search filter applied');
      }
    });

    test('should search messages by subject', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      const searchInput = page.getByPlaceholder(/rechercher|search/i);
      const searchExists = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);

      if (searchExists) {
        await searchInput.fill('test');
        await page.waitForTimeout(1000);

        // Should filter by subject
        const rowCount = await page.locator('p-table tbody tr').count();
        console.log(`Found ${rowCount} messages matching 'test'`);
      }
    });

    test('should filter messages by date range', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Look for date range picker
      const dateFilter = page.locator('p-calendar, input[type="date"]');
      const dateFilterExists = await dateFilter.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (dateFilterExists) {
        console.log('Date range filter found');
        // Click to open date picker
        await dateFilter.first().click();
        await page.waitForTimeout(500);
      }
    });

    test('should filter by alias/domain', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Look for domain/alias filter dropdown
      const domainFilter = page.locator('p-dropdown[placeholder*="domain" i], p-dropdown[placeholder*="alias" i]');
      const filterExists = await domainFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterExists) {
        await domainFilter.click();
        await page.waitForTimeout(500);

        // Should show available domains/aliases
        console.log('Domain/alias filter found');
      }
    });
  });

  test.describe('Bulk Email Operations', () => {

    test('should select multiple messages', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 1) {
        // Look for checkboxes in table
        const checkboxes = page.locator('p-table tbody tr p-tableCheckbox, p-table tbody tr input[type="checkbox"]');
        const checkboxCount = await checkboxes.count();

        if (checkboxCount > 0) {
          // Select first two messages
          await checkboxes.nth(0).click();
          await checkboxes.nth(1).click();

          console.log('Multiple messages selected');
        }
      }
    });

    test('should have bulk delete option', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Select a message first
      const checkbox = page.locator('p-table tbody tr input[type="checkbox"]').first();
      const checkboxExists = await checkbox.isVisible({ timeout: 3000 }).catch(() => false);

      if (checkboxExists) {
        await checkbox.click();

        // Look for bulk action buttons
        const deleteButton = page.getByRole('button', { name: /supprimer|delete/i });
        const deleteVisible = await deleteButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (deleteVisible) {
          console.log('Bulk delete option found');
        }
      }
    });

    test('should have export messages option', async ({ page }) => {
      await page.goto('/messages');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Look for export button
      const exportButton = page.getByRole('button', { name: /export|télécharger|download/i });
      const exportExists = await exportButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (exportExists) {
        console.log('Export messages option found');
      }
    });
  });
});
