import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { AuthService } from '../services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const messageService = inject(MessageService);
  const authService = inject(AuthService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
        let errorMessage = 'An unexpected error occurred';
        let errorDetail = '';

        if (error.error instanceof ErrorEvent) {
          // Client-side error
          errorMessage = 'Network error occurred';
          errorDetail = error.error.message;
        } else {
          // Server-side error
          switch (error.status) {
            case 400:
              errorMessage = 'Bad request';
              if (error.error?.detail) {
                errorDetail = error.error.detail;
              } else if (error.error?.field_errors) {
                // Handle validation errors
                const fieldErrors = error.error.field_errors;
                const errors = Object.keys(fieldErrors).map(key => 
                  `${key}: ${fieldErrors[key].join(', ')}`
                ).join('; ');
                errorDetail = errors;
              }
              break;
            case 401:
              errorMessage = 'Authentication required';
              errorDetail = 'Please log in to continue';
              // Clear auth state and redirect to login
              authService.logout().subscribe();
              router.navigate(['/auth/login']);
              break;
            case 403:
              errorMessage = 'Access denied';
              errorDetail = 'You do not have permission to perform this action';
              break;
            case 404:
              errorMessage = 'Resource not found';
              errorDetail = 'The requested resource could not be found';
              break;
            case 422:
              errorMessage = 'Validation error';
              if (error.error?.detail) {
                errorDetail = error.error.detail;
              }
              break;
            case 429:
              errorMessage = 'Too many requests';
              errorDetail = 'Please wait before making another request';
              break;
            case 500:
              errorMessage = 'Server error';
              errorDetail = 'An internal server error occurred';
              break;
            case 503:
              errorMessage = 'Service unavailable';
              errorDetail = 'The service is temporarily unavailable';
              break;
            default:
              errorMessage = `HTTP Error ${error.status}`;
              errorDetail = error.error?.detail || error.message || 'Unknown error occurred';
          }
        }

        // Show error notification (except for 401 which redirects)
        if (error.status !== 401) {
          messageService.add({
            severity: 'error',
            summary: errorMessage,
            detail: errorDetail,
            life: 5000
          });
        }

        // Return the error to be handled by the component if needed
        return throwError(() => ({
          status: error.status,
          message: errorMessage,
          detail: errorDetail,
          originalError: error
        }));
      })
    );
};