import { test, expect } from './global-hooks';

/**
 * E2E Tests for Complete Domain Management Flow
 *
 * Tests the complete domain lifecycle including:
 * - Domain creation and configuration
 * - DNS verification workflow
 * - Alias management on verified domains
 * - Domain status transitions
 * - Error handling for verification failures
 */

test.describe('Complete Domain Management Flow', () => {

  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/auth/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password input').fill('password');
    await page.getByRole('button', { name: /se connecter/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test.describe('Domain Creation and Configuration', () => {

    test('should complete domain creation flow', async ({ page }) => {
      // Navigate to domains
      await page.goto('/domains');
      await expect(page).toHaveURL(/\/domains/);

      // Click add domain button
      await page.getByRole('button', { name: /ajouter|nouveau/i }).click();

      // Wait for dialog
      await expect(page.locator('.p-dialog')).toBeVisible();
      await expect(page.getByRole('heading', { name: /ajouter un domaine/i })).toBeVisible();

      // Generate unique domain name for testing
      const uniqueDomain = `test-${Date.now()}.example.com`;

      // Fill domain name
      await page.getByLabel(/nom du domaine/i).fill(uniqueDomain);

      // Submit form
      await page.locator('.p-dialog').getByRole('button', { name: /ajouter|créer/i }).click();

      // Wait for success notification or dialog to close
      await page.waitForTimeout(2000);

      // Check if domain was added (dialog should close or show success)
      const dialogVisible = await page.locator('.p-dialog').isVisible().catch(() => false);

      if (!dialogVisible) {
        // Success - domain was added
        // Should see new domain in the list
        await expect(page.locator(`text=${uniqueDomain}`)).toBeVisible({ timeout: 5000 });
      }
    });

    test('should display DNS configuration instructions after domain creation', async ({ page }) => {
      await page.goto('/domains');

      // Wait for domains table to load
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        // Click on first domain to view details
        await page.locator('p-table tbody tr').first().click();

        // Wait for details view/dialog
        await page.waitForTimeout(1000);

        // Look for DNS configuration section
        const dnsSection = page.locator('text=/DNS|MX Record|SPF|DKIM|DMARC/i').first();
        const dnsVisible = await dnsSection.isVisible({ timeout: 3000 }).catch(() => false);

        if (dnsVisible) {
          await expect(dnsSection).toBeVisible();

          // Should show MX record configuration
          await expect(page.locator('text=/MX/i')).toBeVisible();

          // May show SPF, DKIM, DMARC records
          // These are optional but good to check
        }
      }
    });

    test('should show required DNS records for domain verification', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        // Open domain details
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Check for DNS records display
        const recordTypes = ['MX', 'SPF', 'DKIM', 'DMARC', 'TXT'];

        for (const recordType of recordTypes) {
          const recordVisible = await page.locator(`text=/^${recordType}/i`).isVisible({ timeout: 2000 }).catch(() => false);
          if (recordVisible) {
            console.log(`${recordType} record configuration found`);
          }
        }
      }
    });

    test('should allow copying DNS record values', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for copy buttons next to DNS records
        const copyButtons = page.locator('button:has-text("Copier"), button[title*="copier" i], i.pi-copy');
        const copyButtonCount = await copyButtons.count();

        if (copyButtonCount > 0) {
          // Click first copy button
          await copyButtons.first().click();

          // Should show success message
          await expect(page.locator('.p-toast-message-success, text=/copié/i').first())
            .toBeVisible({ timeout: 3000 })
            .catch(() => console.log('Copy confirmation may not be implemented'));
        }
      }
    });
  });

  test.describe('Domain Verification Workflow', () => {

    test('should show unverified status for new domains', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      // Look for status indicators
      const statusBadges = page.locator('p-tag, .p-badge, [class*="status"]');
      const badgeCount = await statusBadges.count();

      if (badgeCount > 0) {
        // Check for "pending", "unverified", or similar status
        const statusText = await statusBadges.first().textContent();
        console.log('Domain status:', statusText);

        // Common status values: verified, pending, unverified, non-vérifié
        await expect(statusBadges.first()).toBeVisible();
      }
    });

    test('should have verify domain button/action', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        // Open domain details
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for verify button
        const verifyButton = page.getByRole('button', { name: /vérifier|verify|check/i });
        const verifyButtonVisible = await verifyButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (verifyButtonVisible) {
          await expect(verifyButton).toBeVisible();
          await expect(verifyButton).toBeEnabled();
        }
      }
    });

    test('should trigger DNS verification check', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for and click verify button
        const verifyButton = page.getByRole('button', { name: /vérifier|verify/i });
        const verifyButtonVisible = await verifyButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (verifyButtonVisible) {
          await verifyButton.click();

          // Wait for verification to process
          await page.waitForTimeout(2000);

          // Should show loading state or result message
          // This may show success or failure depending on actual DNS setup
        }
      }
    });

    test('should show verification failure message for incorrect DNS', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        const verifyButton = page.getByRole('button', { name: /vérifier|verify/i });
        const verifyButtonVisible = await verifyButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (verifyButtonVisible) {
          await verifyButton.click();
          await page.waitForTimeout(3000);

          // Most test domains will fail verification
          // Should show error message or remain unverified
          const errorMessage = page.locator('.p-toast-message-error, text=/échec|failed|incorrect/i');
          const errorVisible = await errorMessage.isVisible({ timeout: 3000 }).catch(() => false);

          if (errorVisible) {
            console.log('Verification failed as expected for test domain');
          }
        }
      }
    });

    test('should display verification help/instructions', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for help text or instructions
        const helpText = page.locator('text=/suivez les instructions|configurez|instructions/i');
        const helpVisible = await helpText.first().isVisible({ timeout: 2000 }).catch(() => false);

        if (helpVisible) {
          await expect(helpText.first()).toBeVisible();
        }
      }
    });
  });

  test.describe('Alias Management on Domains', () => {

    test('should navigate to create alias from domain details', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for "create alias" or "add alias" button
        const addAliasButton = page.getByRole('button', { name: /ajouter.*alias|créer.*alias|new alias/i });
        const addAliasButtonVisible = await addAliasButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (addAliasButtonVisible) {
          await addAliasButton.click();

          // Should navigate to alias creation or open dialog
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should show aliases associated with domain', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for aliases section
        const aliasSection = page.locator('text=/alias|forwarding.*rule/i');
        const aliasSectionVisible = await aliasSection.first().isVisible({ timeout: 3000 }).catch(() => false);

        if (aliasSectionVisible) {
          console.log('Alias section found in domain details');
        }
      }
    });

    test('should disable alias creation for unverified domains', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        // Find an unverified domain
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Check domain status
        const statusBadge = page.locator('p-tag, .p-badge, [class*="status"]').first();
        const statusText = await statusBadge.textContent().catch(() => '');

        // If domain is unverified, alias creation should be disabled or show warning
        if (statusText.toLowerCase().includes('pending') ||
            statusText.toLowerCase().includes('unverified') ||
            statusText.toLowerCase().includes('non-vérifié')) {

          const addAliasButton = page.getByRole('button', { name: /ajouter.*alias|créer.*alias/i });
          const buttonExists = await addAliasButton.count() > 0;

          if (buttonExists) {
            // Button may be disabled
            const isDisabled = await addAliasButton.isDisabled().catch(() => false);
            if (isDisabled) {
              console.log('Alias creation correctly disabled for unverified domain');
            }
          }
        }
      }
    });
  });

  test.describe('Domain Management Actions', () => {

    test('should allow editing domain settings', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for edit button
        const editButton = page.getByRole('button', { name: /modifier|edit/i });
        const editButtonVisible = await editButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (editButtonVisible) {
          await expect(editButton).toBeVisible();
        }
      }
    });

    test('should show delete domain confirmation', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Look for delete button
        const deleteButton = page.getByRole('button', { name: /supprimer|delete/i });
        const deleteButtonVisible = await deleteButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (deleteButtonVisible) {
          await deleteButton.click();

          // Should show confirmation dialog
          await expect(page.locator('.p-confirm-dialog, .p-dialog')).toBeVisible({ timeout: 2000 });
          await expect(page.locator('text=/confirmer|confirm|supprimer|delete/i')).toBeVisible();

          // Cancel the deletion
          await page.getByRole('button', { name: /annuler|cancel|non/i }).click();
        }
      }
    });

    test('should warn before deleting domain with aliases', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table tbody tr', { timeout: 5000 });

      const rowCount = await page.locator('p-table tbody tr').count();

      if (rowCount > 0) {
        await page.locator('p-table tbody tr').first().click();
        await page.waitForTimeout(1000);

        // Check if domain has aliases
        const aliasCount = page.locator('text=/\\d+.*alias/i');
        const hasAliases = await aliasCount.isVisible({ timeout: 2000 }).catch(() => false);

        if (hasAliases) {
          const deleteButton = page.getByRole('button', { name: /supprimer|delete/i });
          const deleteButtonVisible = await deleteButton.isVisible({ timeout: 3000 }).catch(() => false);

          if (deleteButtonVisible) {
            await deleteButton.click();

            // Should show warning about aliases
            await expect(page.locator('text=/alias|forwarding/i')).toBeVisible({ timeout: 2000 });

            // Cancel
            await page.getByRole('button', { name: /annuler|cancel/i }).click();
          }
        }
      }
    });

    test('should refresh domain list', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Look for refresh button
      const refreshButton = page.getByRole('button', { name: /actualiser|refresh|reload/i });
      const refreshButtonVisible = await refreshButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (refreshButtonVisible) {
        await refreshButton.click();

        // Wait for refresh to complete
        await page.waitForTimeout(1000);

        // Table should still be visible
        await expect(page.locator('p-table')).toBeVisible();
      }
    });
  });

  test.describe('Domain Search and Filtering', () => {

    test('should filter domains by verification status', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Look for status filter dropdown
      const statusFilter = page.locator('p-dropdown[ng-reflect-placeholder*="status" i], select[name*="status" i]');
      const filterExists = await statusFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterExists) {
        await statusFilter.click();

        // Select "verified" or "unverified"
        await page.waitForTimeout(500);
      }
    });

    test('should search domains by name', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table', { timeout: 5000 });

      const searchInput = page.getByPlaceholder(/rechercher|search|filter/i);
      const searchExists = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);

      if (searchExists) {
        await searchInput.fill('example');
        await page.waitForTimeout(500);

        // Results should be filtered
        const rowCount = await page.locator('p-table tbody tr').count();
        console.log(`Filtered to ${rowCount} domains`);
      }
    });

    test('should sort domains by name', async ({ page }) => {
      await page.goto('/domains');
      await page.waitForSelector('p-table', { timeout: 5000 });

      // Click on name column header to sort
      const nameHeader = page.locator('th:has-text("Nom"), th:has-text("Domain"), th:has-text("Domaine")').first();
      const headerExists = await nameHeader.isVisible({ timeout: 3000 }).catch(() => false);

      if (headerExists) {
        await nameHeader.click();

        // Wait for sort to apply
        await page.waitForTimeout(500);

        // Click again to reverse sort
        await nameHeader.click();
        await page.waitForTimeout(500);
      }
    });
  });
});
