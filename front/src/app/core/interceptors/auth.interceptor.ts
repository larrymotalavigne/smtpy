import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  
  // Get the auth token from the auth service
  const authToken = authService.getAuthToken();
  
  // If we have a token, clone the request and add the authorization header
  if (authToken) {
    const authRequest = req.clone({
      setHeaders: {
        Authorization: `Bearer ${authToken}`
      }
    });
    return next(authRequest);
  }
  
  // If no token, proceed with the original request
  return next(req);
};