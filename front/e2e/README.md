# SMTPy E2E Tests

End-to-end tests for the SMTPy application using Playwright.

## Overview

These tests validate critical user journeys and scenarios across the SMTPy frontend and backend integration.

## Test Scenarios

### Authentication (`auth.spec.ts`)
- ✅ Display landing page for unauthenticated users
- ✅ Navigate to login page
- ✅ Validate empty form submissions
- ✅ Login with valid credentials (admin/password)
- ✅ Show error for invalid credentials
- ✅ Logout successfully

### Dashboard (`dashboard.spec.ts`)
- ✅ Display dashboard after login
- ✅ Show statistics cards (total emails, domains, etc.)
- ✅ Render time-series charts
- ✅ Display recent activity section
- ✅ Navigate to domains and messages
- ✅ Refresh stats with date range changes
- ✅ Show success rate metric

### Domain Management (`domains.spec.ts`)
- ✅ Display domains list page
- ✅ Open add domain dialog
- ✅ Validate domain name format
- ✅ Filter domains by name
- ✅ Navigate to domain details
- ✅ Display DNS configuration (MX, SPF, DKIM, DMARC)
- ✅ Show domain status (verified/pending)

### Message Management (`messages.spec.ts`)
- ✅ Display messages list with pagination
- ✅ Paginate through messages
- ✅ Filter messages by status
- ✅ View message details
- ✅ Display message metadata (from, to, subject)
- ✅ Sort messages by date
- ✅ Show message count and statistics

### Billing & Subscriptions (`billing.spec.ts`)
- ✅ Display billing page
- ✅ Show available subscription plans (Free, Starter, Professional)
- ✅ Display plan pricing
- ✅ Show plan features list
- ✅ Display current subscription status
- ✅ Show usage limits with progress bars
- ✅ Show upgrade button for free plan
- ✅ Navigate to Stripe customer portal
- ✅ Display billing history/invoices

### Navigation & Layout (`navigation.spec.ts`)
- ✅ Display main navigation menu
- ✅ Navigate to all main sections
- ✅ Show user profile menu
- ✅ Navigate to profile and settings pages
- ✅ Highlight active route
- ✅ Display breadcrumbs on detail pages
- ✅ Toggle dark mode
- ✅ Redirect unauthenticated users to login

## Running Tests

### Prerequisites
1. **Services must be running** using Docker Compose:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```
   This starts:
   - Backend API on `http://localhost:8000`
   - Frontend on `http://localhost:4200`
   - PostgreSQL database on `localhost:5432`
   - SMTP server on `localhost:1025`

2. **Test database seeded** with admin user (admin/password)
   - Seeding happens automatically when API starts
   - Or run manually: `docker exec smtpy-api-dev python scripts/seed_dev_db.py`

### Commands

```bash
# Run all tests (headless)
npm run test:e2e

# Run tests with UI mode (recommended for development)
npm run test:e2e:ui

# Run tests in headed browser (see what's happening)
npm run test:e2e:headed

# Debug mode (step through tests)
npm run test:e2e:debug

# View test report
npm run test:e2e:report
```

### Running Specific Tests

```bash
# Run single test file
npx playwright test auth.spec.ts

# Run tests matching pattern
npx playwright test --grep "should login"

# Run only failed tests
npx playwright test --last-failed
```

## Test Structure

All tests follow this pattern:

1. **Setup**: Login (if needed) and navigate to the page
2. **Action**: Interact with the UI (click, type, select)
3. **Assertion**: Verify expected behavior (URL, visibility, content)

### Login Helper Pattern

Most tests use this authentication flow:

```typescript
test.beforeEach(async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('admin');
  await page.getByLabel(/mot de passe/i).fill('password');
  await page.getByRole('button', { name: /se connecter/i }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
});
```

## Debugging

### Visual Debugging
```bash
# Open Playwright Inspector
npm run test:e2e:debug

# Run with headed browser to see tests execute
npm run test:e2e:headed
```

### Screenshots and Traces
- **Screenshots**: Automatically captured on failure
- **Traces**: Recorded on first retry
- **Location**: `playwright-report/` and `test-results/`

### Common Issues

#### Backend Not Running
```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:4200
```
**Solution**: Start backend with `cd back/api && uvicorn main:create_app --reload --factory`

#### Frontend Not Starting
```
Error: Timed out waiting for http://localhost:4200
```
**Solution**: Ensure frontend dependencies are installed (`cd front && npm install`)

#### Authentication Failures
```
Error: expect(page).toHaveURL(/\/dashboard/) - Expected URL to match /\/dashboard/
```
**Solution**: Verify admin user exists in database with credentials `admin/password`

## CI/CD Integration

E2E tests are automatically run in the CI/CD pipeline on every push and pull request.

### GitHub Actions Workflow

The E2E tests job in `.github/workflows/ci-cd.yml`:
1. **Sets up environment**: Installs Node.js and dependencies
2. **Installs Playwright**: Installs Chromium browser with system dependencies
3. **Starts services**: Brings up all services with Docker Compose
4. **Waits for readiness**: Ensures frontend and API are responsive
5. **Runs tests**: Executes all E2E tests with retries in CI mode
6. **Uploads artifacts**: Saves test reports and screenshots
7. **Shows logs**: Displays container logs on failure for debugging
8. **Cleans up**: Stops and removes all containers

### CI Configuration

- **Workers**: 1 worker in CI (sequential execution for stability)
- **Retries**: 2 retries per test in CI
- **Timeout**: 30 seconds per test
- **Reporters**: HTML and GitHub annotations in CI
- **Test Database Seeding**: Admin user (admin/password) automatically created before tests
- **Quality Gate**: E2E test failures now block deployment (October 28, 2025)

### Viewing Results

After a CI run:
1. Go to the Actions tab in GitHub
2. Click on the workflow run
3. Download the `playwright-report` artifact for detailed HTML report
4. Check the "E2E Tests" job for inline GitHub annotations

## Best Practices

### Selectors
1. Prefer **role-based selectors**: `getByRole('button', { name: /submit/i })`
2. Use **label-based selectors**: `getByLabel(/email/i)`
3. Fallback to **test IDs**: `getByTestId('submit-button')`
4. Avoid **CSS selectors** when possible

### Waits
1. Use **auto-waiting**: Playwright waits automatically for elements
2. Add **explicit timeouts** for slow operations: `{ timeout: 10000 }`
3. Use **waitForTimeout** sparingly (only for animations/transitions)

### Assertions
1. Use **positive assertions**: `toBeVisible()`, `toHaveText()`
2. Add **timeouts** for dynamic content: `{ timeout: 5000 }`
3. Check **conditional visibility**: `if (await element.isVisible())`

### Test Independence
1. Each test should **work in isolation**
2. Use `beforeEach` for **common setup**
3. Clean up **test data** if creating entities

## Coverage

Current test coverage:
- **6 test files** covering major user flows
- **50+ test scenarios** across authentication, CRUD operations, navigation
- **Core features**: 100% covered
- **Edge cases**: Partial coverage (ongoing)

## Future Enhancements

- [ ] Add tests for domain verification workflow
- [ ] Test email forwarding simulation
- [ ] Add performance tests (load times, API response times)
- [ ] Test mobile responsive layout
- [ ] Add accessibility (a11y) tests
- [ ] Test file upload scenarios (if applicable)
- [ ] Add visual regression tests with Percy/Applitools
