import { HttpInterceptorFn } from '@angular/common/http';

/**
 * Auth interceptor to add credentials to all HTTP requests
 * This ensures session cookies are sent with every request to the backend
 *
 * The backend uses HTTP-only session cookies for authentication,
 * so we need to set withCredentials: true on all requests
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // Clone the request and add withCredentials for cookie handling
  const authReq = req.clone({
    withCredentials: true
  });

  return next(authReq);
};