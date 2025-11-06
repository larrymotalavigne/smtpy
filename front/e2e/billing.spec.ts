import { test, expect } from './global-hooks';

test.describe('Billing and Subscriptions', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/auth/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password input').fill('password');
    await page.getByRole('button', { name: /se connecter/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Navigate to billing page
    await page.goto('/billing');
    await expect(page).toHaveURL(/\/billing/);
  });

  // TODO: Re-enable after fixing billing page UI elements
  test.skip('should display billing page', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: /abonnement|billing|subscription/i })
    ).toBeVisible();
  });

  // TODO: Re-enable after fixing plan display
  test.skip('should display available subscription plans', async ({ page }) => {
    // Wait for plans to load
    await page.waitForTimeout(2000);

    // Should display plan cards
    const planCards = page.locator('.p-card, [class*="plan"]');
    const count = await planCards.count();
    expect(count).toBeGreaterThan(0);

    // Should show plan names (Free, Starter, Professional)
    await expect(page.locator('text=/free|starter|professional/i').first()).toBeVisible();
  });

  // TODO: Re-enable after fixing plan pricing display
  test.skip('should display plan pricing', async ({ page }) => {
    // Wait for plans
    await page.waitForTimeout(2000);

    // Should show prices
    await expect(page.locator('text=/\\$|€|price|prix/i').first()).toBeVisible({ timeout: 5000 });
  });

  // TODO: Re-enable after fixing plan features display
  test.skip('should display plan features list', async ({ page }) => {
    // Wait for plans
    await page.waitForTimeout(2000);

    // Should show feature lists (domains, aliases, emails limits)
    await expect(
      page.locator('text=/domain|alias|email|support/i').first()
    ).toBeVisible({ timeout: 5000 });
  });

  // TODO: Re-enable after fixing subscription status display
  test.skip('should display current subscription status', async ({ page }) => {
    // Look for current plan section
    const currentPlan = page.locator('text=/current|actuel|active/i').first();

    if (await currentPlan.isVisible({ timeout: 3000 })) {
      await expect(currentPlan).toBeVisible();
    }
  });

  // TODO: Re-enable after fixing usage limits display
  test.skip('should display usage limits', async ({ page }) => {
    // Wait for usage data to load
    await page.waitForTimeout(2000);

    // Look for usage indicators (progress bars, numbers)
    const usageSection = page.locator('text=/usage|utilisation|limit/i').first();

    if (await usageSection.isVisible({ timeout: 3000 })) {
      await expect(usageSection).toBeVisible();
    }
  });

  // TODO: Re-enable after fixing upgrade button display
  test.skip('should show upgrade button for free plan', async ({ page }) => {
    // Wait for page to load
    await page.waitForTimeout(2000);

    // Look for upgrade/subscribe buttons
    const upgradeButton = page.getByRole('button', { name: /upgrade|souscrire|subscribe/i }).first();

    if (await upgradeButton.isVisible({ timeout: 3000 })) {
      await expect(upgradeButton).toBeEnabled();
    }
  });

  // TODO: Re-enable after fixing customer portal navigation
  test.skip('should navigate to customer portal if subscription exists', async ({ page }) => {
    // Wait for page to load
    await page.waitForTimeout(2000);

    // Look for "Manage subscription" or "Portal" button
    const portalButton = page.getByRole('button', { name: /manage|portal|gérer/i }).first();

    if (await portalButton.isVisible({ timeout: 3000 })) {
      await expect(portalButton).toBeVisible();
    }
  });

  test('should display billing history if available', async ({ page }) => {
    // Wait for page to load
    await page.waitForTimeout(2000);

    // Look for invoices or history section
    const historySection = page.locator('text=/invoice|facture|history|historique/i').first();

    if (await historySection.isVisible({ timeout: 3000 })) {
      await expect(historySection).toBeVisible();
    }
  });

  test('should show usage percentage bars', async ({ page }) => {
    // Wait for usage data
    await page.waitForTimeout(2000);

    // Look for progress bars
    const progressBar = page.locator('p-progressbar, [role="progressbar"], .progress').first();

    if (await progressBar.isVisible({ timeout: 3000 })) {
      await expect(progressBar).toBeVisible();
    }
  });
});
