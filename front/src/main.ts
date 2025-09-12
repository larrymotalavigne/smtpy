import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { importProvidersFrom } from '@angular/core';

// PrimeNG Services
import { MessageService } from 'primeng/api';
import { ConfirmationService } from 'primeng/api';

// Interceptors
import { authInterceptor } from './app/core/interceptors/auth.interceptor';
import { errorInterceptor } from './app/core/interceptors/error.interceptor';

import { AppComponent } from './app/app.component';

// Routes from app-routing.module.ts
const routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full' as const
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./app/features/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'domains',
    loadComponent: () => import('./app/features/domains/domains.component').then(m => m.DomainsComponent)
  },
  {
    path: 'messages',
    loadComponent: () => import('./app/features/messages/messages.component').then(m => m.MessagesComponent)
  },
  {
    path: 'billing',
    loadComponent: () => import('./app/features/billing/billing.component').then(m => m.BillingComponent)
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([authInterceptor, errorInterceptor])
    ),
    provideAnimations(),
    MessageService,
    ConfirmationService
  ]
}).catch(err => console.error(err));