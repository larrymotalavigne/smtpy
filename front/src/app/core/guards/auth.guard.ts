import {inject} from '@angular/core';
import {CanActivateFn, Router} from '@angular/router';
import {AuthService} from '@/core/services/auth.service';
import {catchError, map, take} from 'rxjs/operators';
import {of} from 'rxjs';

/**
 * Auth guard to protect routes that require authentication
 * Revalidates session with backend before allowing access
 * Redirects to landing page if user is not authenticated or session expired
 */
export const authGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // If user appears authenticated, revalidate session with backend
    if (authService.isAuthenticated()) {
        return authService.checkAuthStatus().pipe(
            map(response => {
                if (response.success && response.data) {
                    // Session is valid, allow access
                    return true;
                } else {
                    // Session invalid, redirect to landing page
                    router.navigate(['/']);
                    return false;
                }
            }),
            catchError(() => {
                // Error checking auth status, redirect to landing page
                router.navigate(['/']);
                return of(false);
            })
        );
    } else {
        // User is not authenticated, redirect to landing page immediately
        router.navigate(['/']);
        return of(false);
    }
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
 * Revalidates session with backend and checks admin role before allowing access
 * Redirects to landing page if user is not authenticated
 */
export const adminGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // Check if user appears authenticated first
    if (authService.isAuthenticated()) {
        // Revalidate session and check admin role
        return authService.checkAuthStatus().pipe(
            map(response => {
                const user = response.data;
                if (user && user.role === 'admin') {
                    // User is admin, allow access
                    return true;
                } else if (user) {
                    // User is authenticated but not admin, redirect to dashboard
                    router.navigate(['/dashboard']);
                    return false;
                } else {
                    // Session invalid, redirect to landing page
                    router.navigate(['/']);
                    return false;
                }
            }),
            catchError(() => {
                // Error checking auth status, redirect to landing page
                router.navigate(['/']);
                return of(false);
            })
        );
    } else {
        // User is not authenticated, redirect to landing page immediately
        router.navigate(['/']);
        return of(false);
    }
};
