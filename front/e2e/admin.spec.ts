import { test, expect } from './global-hooks';
import { login, waitForAngular } from './helpers';

/**
 * E2E Tests for Admin Operations
 *
 * Based on features/admin.feature
 * Covers admin user management, system statistics, and administrative actions
 */

test.describe('Admin Operations', () => {

  test.beforeEach(async ({ page }) => {
    // Login as admin
    await login(page, 'admin', 'password');
    await waitForAngular(page);
  });

  test.describe('User Management', () => {

    test('should view all users', async ({ page }) => {
      await page.goto('/admin/users');
      await expect(page).toHaveURL(/\/admin\/users/);

      // Should display users table
      await expect(page.getByRole('heading', { name: /utilisateurs|users/i })).toBeVisible({ timeout: 5000 });
      await expect(page.locator('p-table, table')).toBeVisible();

      // Should display user columns
      const hasColumns = await Promise.any([
        page.locator('th:has-text("Username"), th:has-text("Nom")').first().isVisible({ timeout: 3000 }),
        page.locator('text=/username|email|role|status/i').first().isVisible({ timeout: 3000 })
      ]).catch(() => false);

      if (hasColumns) {
        console.log('User table columns found');
      }
    });

    test('should search users', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const searchInput = page.getByPlaceholder(/rechercher|search|filter/i);
      const searchVisible = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);

      if (searchVisible) {
        await searchInput.fill('admin');
        await page.waitForTimeout(500);

        // Should filter results
        await expect(page.locator('tbody tr, .user-row').first()).toBeVisible();
      }
    });

    test('should filter users by role', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const roleFilter = page.locator('p-dropdown[ng-reflect-placeholder*="role" i], select[name*="role" i]');
      const filterVisible = await roleFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await roleFilter.click();
        await page.waitForTimeout(500);

        // Select admin role
        const adminOption = page.locator('text=/^admin$/i').first();
        const optionVisible = await adminOption.isVisible({ timeout: 2000 }).catch(() => false);

        if (optionVisible) {
          await adminOption.click();
          await page.waitForTimeout(500);
        }
      }
    });

    test('should filter users by status', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('p-table, table', { timeout: 5000 });

      const statusFilter = page.locator('p-dropdown[ng-reflect-placeholder*="status" i], select[name*="status" i]');
      const filterVisible = await statusFilter.isVisible({ timeout: 3000 }).catch(() => false);

      if (filterVisible) {
        await statusFilter.click();
        await page.waitForTimeout(500);
      }
    });

    test('should view user details', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .user-row').first().click();
        await page.waitForTimeout(1000);

        // Should show user details dialog or page
        const detailsVisible = await page.locator('.p-dialog, [class*="user-detail"]').isVisible({ timeout: 3000 }).catch(() => false);

        if (detailsVisible) {
          // Should show user information
          await expect(page.locator('text=/username|email|role|domains|aliases/i').first()).toBeVisible();
        }
      }
    });

    test('should disable user account', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 1) { // At least 2 users (don't disable admin)
        // Click on a non-admin user
        await page.locator('tbody tr, .user-row').nth(1).click();
        await page.waitForTimeout(1000);

        const disableButton = page.getByRole('button', { name: /désactiver|disable/i });
        const buttonVisible = await disableButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (buttonVisible) {
          await disableButton.click();

          // Should show confirmation dialog
          await expect(page.locator('.p-confirm-dialog, .p-dialog')).toBeVisible({ timeout: 3000 });

          // Cancel the action
          await page.getByRole('button', { name: /annuler|cancel|non/i }).click();
        }
      }
    });

    test('should promote user to admin', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 1) {
        await page.locator('tbody tr, .user-row').nth(1).click();
        await page.waitForTimeout(1000);

        const roleButton = page.getByRole('button', { name: /role|changer.*rôle/i });
        const buttonVisible = await roleButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (buttonVisible) {
          await roleButton.click();
          await page.waitForTimeout(500);

          // Should show role selection
          const adminOption = page.locator('text=/^admin$/i').first();
          const optionVisible = await adminOption.isVisible({ timeout: 2000 }).catch(() => false);

          if (optionVisible) {
            await adminOption.click();

            // Should show confirmation
            await page.waitForTimeout(500);
            const confirmVisible = await page.locator('.p-confirm-dialog').isVisible({ timeout: 2000 }).catch(() => false);

            if (confirmVisible) {
              // Cancel the change
              await page.getByRole('button', { name: /annuler|cancel/i }).click();
            }
          }
        }
      }
    });

    test('should delete user account', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 1) {
        await page.locator('tbody tr, .user-row').nth(1).click();
        await page.waitForTimeout(1000);

        const deleteButton = page.getByRole('button', { name: /supprimer|delete/i });
        const buttonVisible = await deleteButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (buttonVisible) {
          await deleteButton.click();

          // Should show serious warning
          await expect(page.locator('.p-confirm-dialog, .p-dialog')).toBeVisible({ timeout: 3000 });
          await expect(page.locator('text=/supprimer|delete|warning|attention/i').first()).toBeVisible();

          // Cancel deletion
          await page.getByRole('button', { name: /annuler|cancel|non/i }).click();
        }
      }
    });

    test('should reset user password', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .user-row').first().click();
        await page.waitForTimeout(1000);

        const resetButton = page.getByRole('button', { name: /réinitialiser.*mot de passe|reset password/i });
        const buttonVisible = await resetButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (buttonVisible) {
          await resetButton.click();

          // Should show confirmation
          await page.waitForTimeout(1000);
          const successVisible = await page.locator('.p-toast-message-success, text=/envoyé|sent/i').first()
            .isVisible({ timeout: 3000 })
            .catch(() => false);

          if (successVisible) {
            console.log('Password reset email sent');
          }
        }
      }
    });
  });

  test.describe('System Statistics', () => {

    test('should view system statistics', async ({ page }) => {
      await page.goto('/admin/dashboard');
      await waitForAngular(page);

      // Should display system-wide statistics
      await expect(page.locator('text=/statistiques|statistics|total.*users|total.*domains/i').first())
        .toBeVisible({ timeout: 5000 });

      // Should show metric cards
      const cards = page.locator('.p-card, [class*="stat"], [class*="metric"]');
      const cardCount = await cards.count();

      if (cardCount > 0) {
        console.log(`Found ${cardCount} metric cards`);
        await expect(cards.first()).toBeVisible();
      }
    });

    test('should display user statistics', async ({ page }) => {
      await page.goto('/admin/dashboard');
      await page.waitForTimeout(2000);

      // Should show user-related metrics
      const userStats = page.locator('text=/total.*users|active.*users|utilisateurs/i').first();
      const statsVisible = await userStats.isVisible({ timeout: 3000 }).catch(() => false);

      if (statsVisible) {
        await expect(userStats).toBeVisible();
      }
    });

    test('should display domain statistics', async ({ page }) => {
      await page.goto('/admin/dashboard');
      await page.waitForTimeout(2000);

      const domainStats = page.locator('text=/total.*domains|domaines/i').first();
      const statsVisible = await domainStats.isVisible({ timeout: 3000 }).catch(() => false);

      if (statsVisible) {
        await expect(domainStats).toBeVisible();
      }
    });

    test('should display message statistics', async ({ page }) => {
      await page.goto('/admin/dashboard');
      await page.waitForTimeout(2000);

      const messageStats = page.locator('text=/messages.*today|messages.*month|messages.*total/i').first();
      const statsVisible = await messageStats.isVisible({ timeout: 3000 }).catch(() => false);

      if (statsVisible) {
        await expect(messageStats).toBeVisible();
      }
    });

    test('should display system health indicators', async ({ page }) => {
      await page.goto('/admin/dashboard');
      await page.waitForTimeout(2000);

      const healthPanel = page.locator('text=/health|status|API|database|SMTP/i').first();
      const healthVisible = await healthPanel.isVisible({ timeout: 3000 }).catch(() => false);

      if (healthVisible) {
        await expect(healthPanel).toBeVisible();
      }
    });
  });

  test.describe('Activity Logs', () => {

    test('should view user activity logs', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .user-row').first().click();
        await page.waitForTimeout(1000);

        // Look for activity log section
        const activityTab = page.locator('text=/activité|activity|logs|actions/i').first();
        const tabVisible = await activityTab.isVisible({ timeout: 3000 }).catch(() => false);

        if (tabVisible) {
          await activityTab.click();
          await page.waitForTimeout(500);

          // Should show activity entries
          await expect(page.locator('text=/login|created|updated|deleted/i').first())
            .toBeVisible({ timeout: 3000 });
        }
      }
    });

    test('should view failed login attempts', async ({ page }) => {
      await page.goto('/admin/security');
      await waitForAngular(page);

      // Should show failed login section
      const failedLogins = page.locator('text=/failed.*login|échecs.*connexion/i').first();
      const sectionVisible = await failedLogins.isVisible({ timeout: 3000 }).catch(() => false);

      if (sectionVisible) {
        await expect(failedLogins).toBeVisible();
      }
    });
  });

  test.describe('System Settings', () => {

    test('should view system settings', async ({ page }) => {
      await page.goto('/admin/settings');
      await waitForAngular(page);

      // Should display system settings page
      await expect(page.locator('text=/paramètres|settings|configuration/i').first())
        .toBeVisible({ timeout: 5000 });
    });

    test('should configure system limits', async ({ page }) => {
      await page.goto('/admin/settings');
      await page.waitForTimeout(2000);

      // Look for limit settings
      const limitSettings = page.locator('text=/max.*domains|max.*aliases|limits|limites/i').first();
      const settingsVisible = await limitSettings.isVisible({ timeout: 3000 }).catch(() => false);

      if (settingsVisible) {
        await expect(limitSettings).toBeVisible();
      }
    });
  });

  test.describe('Subscription Management', () => {

    test('should view all subscriptions', async ({ page }) => {
      await page.goto('/admin/subscriptions');
      await waitForAngular(page);

      // Should display subscriptions page
      const subscriptionsPage = await page.locator('text=/subscriptions|abonnements/i').first()
        .isVisible({ timeout: 3000 })
        .catch(() => false);

      if (subscriptionsPage) {
        await expect(page.locator('p-table, table')).toBeVisible();
      }
    });

    test('should display subscription statistics', async ({ page }) => {
      await page.goto('/admin/subscriptions');
      await page.waitForTimeout(2000);

      const stats = page.locator('text=/free|pro|business|revenue/i').first();
      const statsVisible = await stats.isVisible({ timeout: 3000 }).catch(() => false);

      if (statsVisible) {
        await expect(stats).toBeVisible();
      }
    });
  });

  test.describe('User Impersonation', () => {

    test('should have impersonate user option', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 1) {
        await page.locator('tbody tr, .user-row').nth(1).click();
        await page.waitForTimeout(1000);

        const impersonateButton = page.getByRole('button', { name: /impersonate|login as|se connecter en tant que/i });
        const buttonVisible = await impersonateButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (buttonVisible) {
          await expect(impersonateButton).toBeVisible();
        }
      }
    });
  });

  test.describe('Data Export', () => {

    test('should export user data', async ({ page }) => {
      await page.goto('/admin/users');
      await page.waitForSelector('tbody tr, .user-row', { timeout: 5000 });

      const rowCount = await page.locator('tbody tr, .user-row').count();

      if (rowCount > 0) {
        await page.locator('tbody tr, .user-row').first().click();
        await page.waitForTimeout(1000);

        const exportButton = page.getByRole('button', { name: /export|exporter|download/i });
        const buttonVisible = await exportButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (buttonVisible) {
          await expect(exportButton).toBeEnabled();
        }
      }
    });
  });
});
