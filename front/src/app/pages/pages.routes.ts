import { Routes } from '@angular/router';
import { authGuard } from '../core/guards/auth.guard';

export default [
    {
        path: 'dashboard',
        loadComponent: () => import('./dashboard/dashboard.component').then(m => m.DashboardComponent),
        canActivate: [authGuard]
    },
    {
        path: 'domains',
        loadComponent: () => import('./domains/domains.component').then(m => m.DomainsComponent),
        canActivate: [authGuard]
    },
    {
        path: 'messages',
        loadComponent: () => import('./messages/messages.component').then(m => m.MessagesComponent),
        canActivate: [authGuard]
    },
    {
        path: 'statistics',
        loadComponent: () => import('./statistics/statistics.component').then(m => m.StatisticsComponent),
        canActivate: [authGuard]
    },
    {
        path: 'billing',
        loadComponent: () => import('./billing/billing.component').then(m => m.BillingComponent),
        canActivate: [authGuard]
    },
    {
        path: 'profile',
        loadComponent: () => import('./profile/profile.component').then(m => m.ProfileComponent),
        canActivate: [authGuard]
    },
    {
        path: 'settings',
        loadComponent: () => import('./settings/settings.component').then(m => m.SettingsComponent),
        canActivate: [authGuard]
    }
] as Routes;
