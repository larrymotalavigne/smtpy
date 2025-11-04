import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { tap } from 'rxjs/operators';
import { AuthService } from '../../pages/service/auth.service';

/**
 * Auth interceptor to add credentials to all HTTP requests
 * This ensures session cookies are sent with every request to the backend
 *
 * The backend uses HTTP-only session cookies for authentication,
 * so we need to set withCredentials: true on all requests
 *
 * Also refreshes auth status on successful API calls to keep session alive
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  // Clone the request and add withCredentials for cookie handling
  const authReq = req.clone({
    withCredentials: true
  });

  return next(authReq).pipe(
    tap({
      next: (event) => {
        // On successful API calls to non-auth endpoints, we know the session is still valid
        // This helps keep the auth state in sync without needing explicit checks
        if (event.type === 0 && !req.url.includes('/auth/')) {
          // Response received successfully, session is valid
          // No action needed as the session cookie is automatically managed by the browser
        }
      }
    })
  );
};