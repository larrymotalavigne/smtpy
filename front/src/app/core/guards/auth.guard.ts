import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../../pages/service/auth.service';
import { map, take } from 'rxjs/operators';

/**
 * Auth guard to protect routes that require authentication
 * Redirects to login page if user is not authenticated
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser$.pipe(
    take(1),
    map(user => {
      if (user) {
        // User is authenticated, allow access
        return true;
      } else {
        // User is not authenticated, redirect to login
        router.navigate(['/auth/login'], {
          queryParams: { returnUrl: state.url }
        });
        return false;
      }
    })
  );
};

/**
 * Guest guard to prevent authenticated users from accessing auth pages
 * Redirects to dashboard if user is already authenticated
 */
export const guestGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser$.pipe(
    take(1),
    map(user => {
      if (!user) {
        // User is not authenticated, allow access to auth pages
        return true;
      } else {
        // User is already authenticated, redirect to dashboard
        router.navigate(['/dashboard']);
        return false;
      }
    })
  );
};

/**
 * Admin guard to protect routes that require admin role
 * Redirects to dashboard if user is not an admin
 */
export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser$.pipe(
    take(1),
    map(user => {
      if (user && user.role === 'admin') {
        // User is admin, allow access
        return true;
      } else if (user) {
        // User is authenticated but not admin, redirect to dashboard
        router.navigate(['/dashboard']);
        return false;
      } else {
        // User is not authenticated, redirect to login
        router.navigate(['/auth/login'], {
          queryParams: { returnUrl: state.url }
        });
        return false;
      }
    })
  );
};
