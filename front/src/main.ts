import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { importProvidersFrom } from '@angular/core';

// PrimeNG Services & Theme
import { MessageService } from 'primeng/api';
import { ConfirmationService } from 'primeng/api';
import { providePrimeNG } from 'primeng/config';
import { definePreset } from '@primeuix/themes';

// Interceptors
import { authInterceptor } from './app/core/interceptors/auth.interceptor';
import { errorInterceptor } from './app/core/interceptors/error.interceptor';

// Guards
import { authGuard, guestGuard } from './app/core/guards/auth.guard';

import { AppComponent } from './app/app.component';

// Routes from app-routing.module.ts
const routes = [
  {
    path: '',
    loadComponent: () => import('./app/features/landing/landing.component').then(m => m.LandingComponent)
  },
  {
    path: 'auth/login',
    loadComponent: () => import('./app/features/auth/login/login.component').then(m => m.LoginComponent),
    canActivate: [guestGuard]  // Redirect to dashboard if already authenticated
  },
  {
    path: 'auth/register',
    loadComponent: () => import('./app/features/auth/register/register.component').then(m => m.RegisterComponent),
    canActivate: [guestGuard]  // Redirect to dashboard if already authenticated
  },
  {
    path: 'auth/forgot-password',
    loadComponent: () => import('./app/features/auth/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent),
    canActivate: [guestGuard]  // Redirect to dashboard if already authenticated
  },
  {
    path: 'auth/reset-password',
    loadComponent: () => import('./app/features/auth/reset-password/reset-password.component').then(m => m.ResetPasswordComponent),
    canActivate: [guestGuard]  // Redirect to dashboard if already authenticated
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./app/features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard]  // Require authentication
  },
  {
    path: 'domains',
    loadComponent: () => import('./app/features/domains/domains.component').then(m => m.DomainsComponent),
    canActivate: [authGuard]  // Require authentication
  },
  {
    path: 'messages',
    loadComponent: () => import('./app/features/messages/messages.component').then(m => m.MessagesComponent),
    canActivate: [authGuard]  // Require authentication
  },
  {
    path: 'statistics',
    loadComponent: () => import('./app/features/statistics/statistics.component').then(m => m.StatisticsComponent),
    canActivate: [authGuard]  // Require authentication
  },
  {
    path: 'billing',
    loadComponent: () => import('./app/features/billing/billing.component').then(m => m.BillingComponent),
    canActivate: [authGuard]  // Require authentication
  },
  {
    path: '**',
    redirectTo: ''  // Redirect to landing page instead of dashboard
  }
];

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([authInterceptor, errorInterceptor])
    ),
    provideAnimations(),
    providePrimeNG({
      ripple: true
    }),
    MessageService,
    ConfirmationService
  ]
}).catch(err => console.error(err));