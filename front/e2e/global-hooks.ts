import { test as base } from '@playwright/test';
import { setupMockApi } from './helpers';

/**
 * Extend Playwright test to automatically setup mock API for all tests
 */
export const test = base.extend({
  page: async ({ page }, use) => {
    // Setup mock API before each test
    await setupMockApi(page);
    // Use the page
    await use(page);
  },
});

export { expect } from '@playwright/test';
