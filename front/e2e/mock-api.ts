import { Page } from '@playwright/test';

/**
 * Mock API responses for E2E tests
 * This allows tests to run without a real backend
 */
export async function mockApiResponses(page: Page) {
  const apiUrl = 'http://localhost:8000';

  // Mock auth/me endpoint (used to check if user is authenticated)
  await page.route(`${apiUrl}/auth/me`, async (route) => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        error: 'Not authenticated'
      })
    });
  });

  // Mock auth/register endpoint
  await page.route(`${apiUrl}/auth/register`, async (route) => {
    const request = route.request();
    if (request.method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            user: {
              id: 1,
              username: 'testuser',
              email: 'test@example.com',
              is_active: true,
              role: 'user',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          }
        })
      });
    }
  });

  // Mock auth/login endpoint
  await page.route(`${apiUrl}/auth/login`, async (route) => {
    const request = route.request();
    if (request.method() === 'POST') {
      const postData = request.postDataJSON();

      // Check for valid credentials
      if (postData.username === 'admin' && postData.password === 'password') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: {
              user: {
                id: 1,
                username: 'admin',
                email: 'admin@example.com',
                is_active: true,
                role: 'admin',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              }
            }
          })
        });
      } else {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            error: 'Invalid credentials'
          })
        });
      }
    }
  });

  // Mock auth/logout endpoint
  await page.route(`${apiUrl}/auth/logout`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: null
      })
    });
  });

  // Mock password reset request endpoint
  await page.route(`${apiUrl}/auth/request-password-reset`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          message: 'Password reset email sent'
        }
      })
    });
  });

  // Mock password reset endpoint
  await page.route(`${apiUrl}/auth/reset-password`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          message: 'Password reset successful'
        }
      })
    });
  });

  // Mock domains endpoint
  await page.route(`${apiUrl}/domains**`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: []
        })
      });
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 1,
            name: 'example.com',
            verified: false,
            created_at: new Date().toISOString()
          }
        })
      });
    }
  });

  // Mock messages endpoint
  await page.route(`${apiUrl}/messages**`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: []
      })
    });
  });

  // Mock aliases endpoint
  await page.route(`${apiUrl}/aliases**`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: []
        })
      });
    }
  });

  // Mock billing/status endpoint
  await page.route(`${apiUrl}/billing/status`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          has_subscription: false,
          plan: null
        }
      })
    });
  });

  // Mock dashboard/stats endpoint
  await page.route(`${apiUrl}/dashboard/stats`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          total_domains: 0,
          total_aliases: 0,
          total_messages: 0,
          messages_today: 0
        }
      })
    });
  });

  // Mock users/profile endpoint
  await page.route(`${apiUrl}/users/profile`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            is_active: true,
            role: 'admin',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        })
      });
    } else if (route.request().method() === 'PUT') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            is_active: true,
            role: 'admin',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        })
      });
    }
  });

  // Catch-all for other API requests
  await page.route(`${apiUrl}/**`, async (route) => {
    console.log(`[Mock API] Unhandled request: ${route.request().method()} ${route.request().url()}`);
    await route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        error: 'Not found'
      })
    });
  });
}
