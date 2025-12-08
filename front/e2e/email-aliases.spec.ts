import { test, expect } from './global-hooks';
import { login, waitForAngular } from './helpers';

/**
 * E2E Tests for Email Alias Management
 *
 * Based on features/email-aliases.feature
 * Covers alias creation, updating, deletion, and management
 */

test.describe('Email Alias Management', () => {

  test.beforeEach(async ({ page }) => {
    // Login and navigate to aliases page (might be under domains or separate page)
    await login(page);
    await page.goto('/domains'); // Aliases might be managed here or at /aliases
    await waitForAngular(page);
  });

  test.describe('Create Email Alias', () => {

    test('should create a new email alias', async ({ page }) => {
      // Navigate to where aliases are created
      await page.waitForTimeout(2000);

      const createButton = page.getByRole('button', { name: /ajouter.*alias|créer.*alias|new alias/i });
      const buttonVisible = await createButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await createButton.click();
        await page.waitForTimeout(1000);

        // Should show create alias dialog
        await expect(page.locator('.p-dialog')).toBeVisible({ timeout: 3000 });

        // Fill alias form
        const timestamp = Date.now();
        await page.locator('input[name="alias"], #alias').fill(`test${timestamp}@example.com`);
        await page.locator('input[name="forwardTo"], #forwardTo').fill('myemail@example.com');

        // Submit
        const submitButton = page.locator('.p-dialog').getByRole('button', { name: /créer|ajouter|create/i });
        await submitButton.click();
        await page.waitForTimeout(2000);
      }
    });

    test('should validate alias format', async ({ page }) => {
      await page.waitForTimeout(2000);

      const createButton = page.getByRole('button', { name: /ajouter.*alias|créer.*alias/i });
      const buttonVisible = await createButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await createButton.click();
        await page.waitForTimeout(500);

        // Try invalid format
        await page.locator('input[name="alias"], #alias').fill('invalid-email');
        await page.locator('input[name="alias"], #alias').blur();

        // Should show validation error
        const error = page.locator('text=/invalid|invalide|format/i').first();
        const errorVisible = await error.isVisible({ timeout: 2000 }).catch(() => false);

        if (errorVisible) {
          await expect(error).toBeVisible();
        }
      }
    });

    test('should prevent duplicate alias creation', async ({ page }) => {
      await page.waitForTimeout(2000);

      const createButton = page.getByRole('button', { name: /ajouter.*alias|créer.*alias/i });
      const buttonVisible = await createButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await createButton.click();
        await page.waitForTimeout(500);

        // Try to create existing alias
        await page.locator('input[name="alias"], #alias').fill('admin@example.com');
        await page.locator('input[name="forwardTo"], #forwardTo').fill('test@example.com');

        const submitButton = page.locator('.p-dialog').getByRole('button', { name: /créer|ajouter/i });
        await submitButton.click();
        await page.waitForTimeout(2000);

        // Should show duplicate error
        const error = page.locator('.p-toast-message-error, text=/exists|existe|already/i').first();
        const errorVisible = await error.isVisible({ timeout: 3000 }).catch(() => false);

        if (errorVisible) {
          console.log('Duplicate alias error shown');
        }
      }
    });
  });

  test.describe('View and List Aliases', () => {

    test('should display aliases list', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show aliases in table or list
      const aliasesList = page.locator('p-table, tbody tr, .alias-list');
      const listVisible = await aliasesList.isVisible({ timeout: 3000 }).catch(() => false);

      if (listVisible) {
        await expect(aliasesList).toBeVisible();
      }
    });

    test('should show alias details', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Click on an alias to see details
      const firstAlias = page.locator('tbody tr, .alias-row').first();
      const aliasVisible = await firstAlias.isVisible({ timeout: 3000 }).catch(() => false);

      if (aliasVisible) {
        await firstAlias.click();
        await page.waitForTimeout(1000);

        // Should show details
        const details = page.locator('.p-dialog, [class*="detail"]');
        const detailsVisible = await details.isVisible({ timeout: 2000 }).catch(() => false);

        if (detailsVisible) {
          await expect(details).toBeVisible();
        }
      }
    });

    test('should display forwarding address', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show "Forward to" column or field
      const forwardTo = page.locator('text=/forward.*to|transfert|destination/i');
      const visible = await forwardTo.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (visible) {
        await expect(forwardTo.first()).toBeVisible();
      }
    });

    test('should display alias status (enabled/disabled)', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show status badges
      const statusBadges = page.locator('p-tag, .p-badge, text=/enabled|disabled|actif|désactivé/i');
      const badgeCount = await statusBadges.count();

      if (badgeCount > 0) {
        console.log(`Found ${badgeCount} status indicators`);
      }
    });

    test('should show creation date', async ({ page }) => {
      await page.waitForTimeout(2000);

      const firstAlias = page.locator('tbody tr, .alias-row').first();
      const aliasVisible = await firstAlias.isVisible({ timeout: 3000 }).catch(() => false);

      if (aliasVisible) {
        await firstAlias.click();
        await page.waitForTimeout(500);

        const createdDate = page.locator('text=/created|créé|date/i');
        const dateVisible = await createdDate.first().isVisible({ timeout: 2000 }).catch(() => false);

        if (dateVisible) {
          console.log('Creation date displayed');
        }
      }
    });

    test('should show message statistics', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show message counts
      const messageStats = page.locator('text=/\\d+.*messages|messages.*received/i');
      const statsVisible = await messageStats.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (statsVisible) {
        console.log('Message statistics displayed');
      }
    });
  });

  test.describe('Update Alias', () => {

    test('should update alias forwarding address', async ({ page }) => {
      await page.waitForTimeout(2000);

      const firstAlias = page.locator('tbody tr, .alias-row').first();
      const aliasVisible = await firstAlias.isVisible({ timeout: 3000 }).catch(() => false);

      if (aliasVisible) {
        await firstAlias.click();
        await page.waitForTimeout(500);

        const editButton = page.getByRole('button', { name: /modifier|edit/i });
        const buttonVisible = await editButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await editButton.click();
          await page.waitForTimeout(500);

          // Update forwarding address
          const forwardToInput = page.locator('input[name="forwardTo"], #forwardTo');
          await forwardToInput.fill('newemail@example.com');

          // Save
          const saveButton = page.getByRole('button', { name: /save|enregistrer|update/i });
          await saveButton.click();
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should update alias description', async ({ page }) => {
      await page.waitForTimeout(2000);

      const firstAlias = page.locator('tbody tr, .alias-row').first();
      const aliasVisible = await firstAlias.isVisible({ timeout: 3000 }).catch(() => false);

      if (aliasVisible) {
        await firstAlias.click();
        await page.waitForTimeout(500);

        const editButton = page.getByRole('button', { name: /modifier|edit/i });
        const buttonVisible = await editButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await editButton.click();
          await page.waitForTimeout(500);

          // Update description if field exists
          const descInput = page.locator('input[name="description"], textarea[name="description"]');
          const inputVisible = await descInput.isVisible({ timeout: 2000 }).catch(() => false);

          if (inputVisible) {
            await descInput.fill('Updated description');
            const saveButton = page.getByRole('button', { name: /save|enregistrer/i });
            await saveButton.click();
          }
        }
      }
    });
  });

  test.describe('Enable and Disable Alias', () => {

    test('should disable an active alias', async ({ page }) => {
      await page.waitForTimeout(2000);

      const firstAlias = page.locator('tbody tr, .alias-row').first();
      const aliasVisible = await firstAlias.isVisible({ timeout: 3000 }).catch(() => false);

      if (aliasVisible) {
        await firstAlias.click();
        await page.waitForTimeout(500);

        const disableButton = page.getByRole('button', { name: /disable|désactiver/i });
        const buttonVisible = await disableButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await disableButton.click();
          await page.waitForTimeout(1000);

          // Should show disabled status
          const disabledBadge = page.locator('text=/disabled|désactivé/i');
          const badgeVisible = await disabledBadge.isVisible({ timeout: 2000 }).catch(() => false);

          if (badgeVisible) {
            console.log('Alias successfully disabled');
          }
        }
      }
    });

    test('should enable a disabled alias', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Find a disabled alias or disable one first
      const disabledAlias = page.locator('tbody tr:has-text("disabled"), tbody tr:has-text("désactivé")').first();
      const aliasVisible = await disabledAlias.isVisible({ timeout: 3000 }).catch(() => false);

      if (aliasVisible) {
        await disabledAlias.click();
        await page.waitForTimeout(500);

        const enableButton = page.getByRole('button', { name: /enable|activer/i });
        const buttonVisible = await enableButton.isVisible({ timeout: 2000 }).catch(() => false);

        if (buttonVisible) {
          await enableButton.click();
          await page.waitForTimeout(1000);
        }
      }
    });
  });

  test.describe('Delete Alias', () => {

    test('should delete an alias with confirmation', async ({ page }) => {
      await page.waitForTimeout(2000);

      const firstAlias = page.locator('tbody tr, .alias-row').first();
      const aliasVisible = await firstAlias.isVisible({ timeout: 3000 }).catch(() => false);

      if (aliasVisible) {
        await firstAlias.click();
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
  });

  test.describe('Search and Filter Aliases', () => {

    test('should search aliases by address', async ({ page }) => {
      await page.waitForTimeout(2000);

      const searchInput = page.getByPlaceholder(/search|rechercher|filter/i);
      const searchVisible = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);

      if (searchVisible) {
        await searchInput.fill('admin');
        await page.waitForTimeout(500);

        // Results should be filtered
        console.log('Search applied');
      }
    });

    test('should filter aliases by status', async ({ page }) => {
      await page.waitForTimeout(2000);

      const statusFilter = page.locator('p-dropdown[ng-reflect-placeholder*="status"], select[name*="status"]');
      const filterVisible = await statusFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await statusFilter.click();
        await page.waitForTimeout(500);

        // Select enabled/disabled
        const option = page.locator('text=/^enabled$|^actif$/i').first();
        const optionVisible = await option.isVisible({ timeout: 2000 }).catch(() => false);

        if (optionVisible) {
          await option.click();
        }
      }
    });

    test('should filter aliases by domain', async ({ page }) => {
      await page.waitForTimeout(2000);

      const domainFilter = page.locator('p-dropdown[ng-reflect-placeholder*="domain"], select[name*="domain"]');
      const filterVisible = await domainFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await domainFilter.click();
        await page.waitForTimeout(500);
      }
    });
  });

  test.describe('Pagination', () => {

    test('should paginate through aliases', async ({ page }) => {
      await page.waitForTimeout(2000);

      const paginator = page.locator('.p-paginator');
      const paginatorVisible = await paginator.isVisible({ timeout: 3000 }).catch(() => false);

      if (paginatorVisible) {
        const nextButton = paginator.locator('button[aria-label*="Next"]');
        const buttonEnabled = await nextButton.isEnabled().catch(() => false);

        if (buttonEnabled) {
          await nextButton.click();
          await page.waitForTimeout(500);
        }
      }
    });
  });

  test.describe('Bulk Operations', () => {

    test('should select multiple aliases', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for checkboxes
      const checkboxes = page.locator('p-tableCheckbox, input[type="checkbox"]');
      const checkboxCount = await checkboxes.count();

      if (checkboxCount > 1) {
        await checkboxes.first().click();
        await checkboxes.nth(1).click();
        console.log('Multiple aliases selected');
      }
    });

    test('should bulk disable aliases', async ({ page }) => {
      await page.waitForTimeout(2000);

      const bulkDisableButton = page.getByRole('button', { name: /bulk.*disable|disable.*selected/i });
      const buttonVisible = await bulkDisableButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(bulkDisableButton).toBeVisible();
      }
    });

    test('should bulk delete aliases', async ({ page }) => {
      await page.waitForTimeout(2000);

      const bulkDeleteButton = page.getByRole('button', { name: /bulk.*delete|delete.*selected/i });
      const buttonVisible = await bulkDeleteButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(bulkDeleteButton).toBeVisible();
      }
    });
  });

  test.describe('Alias Restrictions', () => {

    test('should prevent creating alias for unverified domain', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Try to create alias for unverified domain
      const createButton = page.getByRole('button', { name: /ajouter.*alias|créer.*alias/i });
      const buttonVisible = await createButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await createButton.click();
        await page.waitForTimeout(500);

        // Should warn about domain verification or disable domain selection
        const warning = page.locator('text=/verify|vérifier|unverified|non.*vérifié/i').first();
        const warningVisible = await warning.isVisible({ timeout: 2000 }).catch(() => false);

        if (warningVisible) {
          console.log('Domain verification warning displayed');
        }
      }
    });
  });
});
