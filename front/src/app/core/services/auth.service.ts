import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap, catchError, of, interval, Subscription } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../../core/interfaces/common.interface';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: 'admin' | 'user';
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  access_token?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService implements OnDestroy {
  private apiUrl = `${environment.apiUrl}/auth`;
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private authCheckSubscription?: Subscription;

  // Check auth status every 5 minutes to detect session expiration
  private readonly AUTH_CHECK_INTERVAL = 5 * 60 * 1000;

  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {
    // Set up periodic auth status checks
    // Note: Initial auth check is handled by APP_INITIALIZER in app.config.ts
    this.startPeriodicAuthCheck();
  }

  ngOnDestroy(): void {
    this.stopPeriodicAuthCheck();
  }

  private startPeriodicAuthCheck(): void {
    // Check auth status periodically to detect session expiration
    this.authCheckSubscription = interval(this.AUTH_CHECK_INTERVAL).subscribe(() => {
      if (this.isAuthenticated()) {
        this.checkAuthStatus().subscribe({
          error: () => {
            // Session expired or error occurred
            // The error interceptor will handle the redirect
          }
        });
      }
    });
  }

  private stopPeriodicAuthCheck(): void {
    if (this.authCheckSubscription) {
      this.authCheckSubscription.unsubscribe();
    }
  }

  login(credentials: LoginRequest): Observable<ApiResponse<AuthResponse>> {
    return this.http.post<ApiResponse<AuthResponse>>(`${this.apiUrl}/login`, credentials)
      .pipe(
        tap(response => {
          if (response.success && response.data?.user) {
            this.currentUserSubject.next(response.data.user);
            // Session is managed via HTTP-only cookies by the auth interceptor
          }
        })
      );
  }

  register(userData: RegisterRequest): Observable<ApiResponse<AuthResponse>> {
    return this.http.post<ApiResponse<AuthResponse>>(`${this.apiUrl}/register`, userData)
      .pipe(
        tap(response => {
          if (response.success && response.data?.user) {
            this.currentUserSubject.next(response.data.user);
          }
        })
      );
  }

  logout(): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}/logout`, {})
      .pipe(
        tap(() => {
          this.currentUserSubject.next(null);
        }),
        catchError(() => {
          // Even if logout fails on server, clear local state
          this.currentUserSubject.next(null);
          return of({ success: true, data: null });
        })
      );
  }

  checkAuthStatus(): Observable<ApiResponse<User>> {
    return this.http.get<ApiResponse<User>>(`${this.apiUrl}/me`)
      .pipe(
        tap(response => {
          if (response.success && response.data) {
            this.currentUserSubject.next(response.data);
          } else {
            this.currentUserSubject.next(null);
          }
        }),
        catchError(() => {
          this.currentUserSubject.next(null);
          return of({ success: false, data: undefined });
        })
      );
  }

  requestPasswordReset(email: string): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}/request-password-reset`, { email });
  }

  resetPassword(token: string, newPassword: string): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}/reset-password`, {
      token,
      new_password: newPassword
    });
  }

  isAuthenticated(): boolean {
    return this.currentUserSubject.value !== null;
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user?.role === 'admin';
  }
}