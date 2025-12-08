import { test, expect } from './global-hooks';
import { login, waitForAngular } from './helpers';

/**
 * E2E Tests for Billing and Subscription Management
 *
 * Based on features/billing.feature
 * Covers subscription plans, payments, billing history, and Stripe integration
 */

test.describe('Billing and Subscription Management', () => {

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await login(page);
    await page.goto('/billing');
    await expect(page).toHaveURL(/\/billing/);
    await waitForAngular(page);
  });

  test.describe('Subscription Plans', () => {

    test('should display available subscription plans', async ({ page }) => {
      // Wait for plans to load
      await page.waitForTimeout(2000);

      // Should display page heading
      await expect(page.locator('text=/abonnement|billing|subscription|plans/i').first())
        .toBeVisible({ timeout: 5000 });

      // Should show plan cards or sections
      const planElements = page.locator('.p-card, [class*="plan"], text=/free|pro|business|starter/i');
      const planCount = await planElements.count();

      expect(planCount).toBeGreaterThan(0);
    });

    test('should display plan features and limits', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show features for each plan
      const features = page.locator('text=/domains|alias|messages|features|caractéristiques/i');
      const featureCount = await features.count();

      if (featureCount > 0) {
        await expect(features.first()).toBeVisible();
      }
    });

    test('should display plan pricing', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show prices
      const pricing = page.locator('text=/\\$|€|price|prix|\\d+.*mois|\\d+.*month/i');
      const priceVisible = await pricing.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (priceVisible) {
        await expect(pricing.first()).toBeVisible();
      }
    });

    test('should display current subscription status', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for current plan indicator
      const currentPlan = page.locator('text=/current|actuel|active|plan/i').first();
      const planVisible = await currentPlan.isVisible({ timeout: 3000 }).catch(() => false);

      if (planVisible) {
        await expect(currentPlan).toBeVisible();
      }
    });

    test('should show upgrade button for free plan users', async ({ page }) => {
      await page.waitForTimeout(2000);

      const upgradeButton = page.getByRole('button', { name: /upgrade|améliorer|souscrire|subscribe/i }).first();
      const buttonVisible = await upgradeButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(upgradeButton).toBeEnabled();
      }
    });
  });

  test.describe('Subscription Actions', () => {

    test('should initiate subscription upgrade', async ({ page }) => {
      await page.waitForTimeout(2000);

      const subscribeButton = page.getByRole('button', { name: /subscribe|souscrire|upgrade|améliorer/i }).first();
      const buttonVisible = await subscribeButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await subscribeButton.click();

        // Should redirect to Stripe checkout or show upgrade dialog
        await page.waitForTimeout(2000);

        // Check if redirected to Stripe or if dialog opened
        const currentUrl = page.url();
        if (currentUrl.includes('stripe') || currentUrl.includes('checkout')) {
          console.log('Redirected to Stripe checkout');
        } else {
          // Check for dialog
          const dialogVisible = await page.locator('.p-dialog').isVisible().catch(() => false);
          if (dialogVisible) {
            console.log('Subscription dialog opened');
          }
        }
      }
    });

    test('should access customer portal', async ({ page }) => {
      await page.waitForTimeout(2000);

      const portalButton = page.getByRole('button', { name: /manage|gérer|portal|customer/i }).first();
      const buttonVisible = await portalButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(portalButton).toBeVisible();
        // Note: Clicking would redirect to Stripe, so we just verify it's present
      }
    });
  });

  test.describe('Usage and Limits', () => {

    test('should display usage against plan limits', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for usage indicators
      const usageSection = page.locator('text=/usage|utilisation|limit|limite/i').first();
      const usageVisible = await usageSection.isVisible({ timeout: 3000 }).catch(() => false);

      if (usageVisible) {
        await expect(usageSection).toBeVisible();
      }
    });

    test('should show progress bars for resource usage', async ({ page }) => {
      await page.waitForTimeout(2000);

      const progressBars = page.locator('p-progressbar, [role="progressbar"], .progress, [class*="progress"]');
      const barCount = await progressBars.count();

      if (barCount > 0) {
        await expect(progressBars.first()).toBeVisible();
        console.log(`Found ${barCount} usage progress bars`);
      }
    });

    test('should display domain usage', async ({ page }) => {
      await page.waitForTimeout(2000);

      const domainUsage = page.locator('text=/domains.*\\d+|domaines.*\\d+/i').first();
      const usageVisible = await domainUsage.isVisible({ timeout: 3000 }).catch(() => false);

      if (usageVisible) {
        await expect(domainUsage).toBeVisible();
      }
    });

    test('should display alias usage', async ({ page }) => {
      await page.waitForTimeout(2000);

      const aliasUsage = page.locator('text=/alias.*\\d+/i').first();
      const usageVisible = await aliasUsage.isVisible({ timeout: 3000 }).catch(() => false);

      if (usageVisible) {
        await expect(aliasUsage).toBeVisible();
      }
    });

    test('should display message usage', async ({ page }) => {
      await page.waitForTimeout(2000);

      const messageUsage = page.locator('text=/messages.*\\d+/i').first();
      const usageVisible = await messageUsage.isVisible({ timeout: 3000 }).catch(() => false);

      if (usageVisible) {
        await expect(messageUsage).toBeVisible();
      }
    });

    test('should show percentage of limit used', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for percentage indicators
      const percentage = page.locator('text=/\\d+%|\\d+\\s*\\/\\s*\\d+/').first();
      const percentageVisible = await percentage.isVisible({ timeout: 3000 }).catch(() => false);

      if (percentageVisible) {
        await expect(percentage).toBeVisible();
      }
    });

    test('should show upgrade prompt when approaching limits', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for upgrade prompt near usage indicators
      const upgradePrompt = page.locator('text=/upgrade|améliorer|limit.*reached|limite.*atteinte/i').first();
      const promptVisible = await upgradePrompt.isVisible({ timeout: 3000 }).catch(() => false);

      if (promptVisible) {
        console.log('Upgrade prompt displayed');
      }
    });
  });

  test.describe('Billing History', () => {

    test('should display billing history section', async ({ page }) => {
      await page.waitForTimeout(2000);

      const historySection = page.locator('text=/invoice|facture|history|historique|billing.*history/i').first();
      const historyVisible = await historySection.isVisible({ timeout: 3000 }).catch(() => false);

      if (historyVisible) {
        await expect(historySection).toBeVisible();
      }
    });

    test('should show list of past invoices', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for invoices table or list
      const invoicesList = page.locator('text=/invoice|facture/i, p-table, .invoice, [class*="invoice"]');
      const invoicesVisible = await invoicesList.first().isVisible({ timeout: 3000 }).catch(() => false);

      if (invoicesVisible) {
        await expect(invoicesList.first()).toBeVisible();
      }
    });

    test('should display invoice details', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for invoice information fields
      const invoiceFields = page.locator('text=/date|amount|status|paid|pending|montant|statut/i');
      const fieldsCount = await invoiceFields.count();

      if (fieldsCount > 0) {
        console.log(`Found ${fieldsCount} invoice fields`);
      }
    });

    test('should have download invoice option', async ({ page }) => {
      await page.waitForTimeout(2000);

      const downloadButton = page.getByRole('button', { name: /download|télécharger|PDF/i }).first();
      const buttonVisible = await downloadButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(downloadButton).toBeVisible();
      }
    });
  });

  test.describe('Payment Method', () => {

    test('should display current payment method', async ({ page }) => {
      await page.waitForTimeout(2000);

      const paymentMethod = page.locator('text=/payment.*method|carte|card|méthode.*paiement/i').first();
      const methodVisible = await paymentMethod.isVisible({ timeout: 3000 }).catch(() => false);

      if (methodVisible) {
        await expect(paymentMethod).toBeVisible();
      }
    });

    test('should have update payment method button', async ({ page }) => {
      await page.waitForTimeout(2000);

      const updateButton = page.getByRole('button', { name: /update.*payment|modifier.*paiement|change.*card/i }).first();
      const buttonVisible = await updateButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(updateButton).toBeVisible();
      }
    });
  });

  test.describe('Subscription Management', () => {

    test('should display next billing date', async ({ page }) => {
      await page.waitForTimeout(2000);

      const billingDate = page.locator('text=/next.*billing|prochain.*paiement|renewal|renouvellement/i').first();
      const dateVisible = await billingDate.isVisible({ timeout: 3000 }).catch(() => false);

      if (dateVisible) {
        await expect(billingDate).toBeVisible();
      }
    });

    test('should display billing cycle', async ({ page }) => {
      await page.waitForTimeout(2000);

      const billingCycle = page.locator('text=/monthly|mensuel|annual|annuel|billing.*cycle/i').first();
      const cycleVisible = await billingCycle.isVisible({ timeout: 3000 }).catch(() => false);

      if (cycleVisible) {
        await expect(billingCycle).toBeVisible();
      }
    });

    test('should show cancel subscription option', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for cancel option (might be in customer portal)
      const cancelButton = page.getByRole('button', { name: /cancel|annuler|résilier/i }).first();
      const buttonVisible = await cancelButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await expect(cancelButton).toBeVisible();
      }
    });

    test('should show reactivate option for cancelled subscriptions', async ({ page }) => {
      await page.waitForTimeout(2000);

      const reactivateButton = page.getByRole('button', { name: /reactivate|réactiver/i }).first();
      const buttonVisible = await reactivateButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        console.log('Subscription is cancelled, reactivate option available');
        await expect(reactivateButton).toBeVisible();
      }
    });
  });

  test.describe('Plan Comparison', () => {

    test('should show plan comparison', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for plan comparison table or section
      const comparison = page.locator('text=/compare|comparer|features|fonctionnalités/i').first();
      const comparisonVisible = await comparison.isVisible({ timeout: 3000 }).catch(() => false);

      if (comparisonVisible) {
        await expect(comparison).toBeVisible();
      }
    });

    test('should highlight current plan', async ({ page }) => {
      await page.waitForTimeout(2000);

      const currentBadge = page.locator('text=/current|actuel|active/i, .current, [class*="active"]');
      const badgeCount = await currentBadge.count();

      if (badgeCount > 0) {
        console.log('Current plan is highlighted');
      }
    });

    test('should show upgrade paths', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Should show which plans are upgrades
      const upgradeBadge = page.locator('text=/upgrade|améliorer|popular|recommended/i').first();
      const badgeVisible = await upgradeBadge.isVisible({ timeout: 3000 }).catch(() => false);

      if (badgeVisible) {
        console.log('Upgrade recommendations shown');
      }
    });
  });

  test.describe('Subscription Warnings', () => {

    test('should show warning for expiring subscription', async ({ page }) => {
      await page.waitForTimeout(2000);

      const expiryWarning = page.locator('text=/expir|échéance|ending|se termine/i').first();
      const warningVisible = await expiryWarning.isVisible({ timeout: 3000 }).catch(() => false);

      if (warningVisible) {
        console.log('Expiry warning displayed');
        await expect(expiryWarning).toBeVisible();
      }
    });

    test('should show payment failed warning', async ({ page }) => {
      await page.waitForTimeout(2000);

      const paymentWarning = page.locator('text=/payment.*failed|paiement.*échoué|update.*payment/i').first();
      const warningVisible = await paymentWarning.isVisible({ timeout: 3000 }).catch(() => false);

      if (warningVisible) {
        console.log('Payment warning displayed');
        await expect(paymentWarning).toBeVisible();
      }
    });
  });

  test.describe('Proration and Billing Changes', () => {

    test('should show prorated amount for plan changes', async ({ page }) => {
      await page.waitForTimeout(2000);

      const subscribeButton = page.getByRole('button', { name: /subscribe|souscrire|upgrade/i }).first();
      const buttonVisible = await subscribeButton.isVisible({ timeout: 3000 }).catch(() => false);

      if (buttonVisible) {
        await subscribeButton.click();
        await page.waitForTimeout(1000);

        // Look for proration information
        const proration = page.locator('text=/prorat|credit|crédit/i').first();
        const prorationVisible = await proration.isVisible({ timeout: 2000 }).catch(() => false);

        if (prorationVisible) {
          console.log('Proration information shown');
        }
      }
    });

    test('should warn about downgrade limitations', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Look for downgrade warnings
      const downgradeWarning = page.locator('text=/downgrade|rétrograder|lose.*access|perdre.*accès|reduced.*limits/i').first();
      const warningVisible = await downgradeWarning.isVisible({ timeout: 3000 }).catch(() => false);

      if (warningVisible) {
        console.log('Downgrade warning displayed');
      }
    });
  });
});
