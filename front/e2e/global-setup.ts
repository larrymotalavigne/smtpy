/**
 * Global setup for E2E tests
 * This runs once before all tests
 */
export default async function globalSetup() {
  console.log('='.repeat(80));
  console.log('E2E Tests - Mock Backend Mode');
  console.log('='.repeat(80));
  console.log('All API requests will be mocked to allow tests to run without a backend.');
  console.log('='.repeat(80));
}
