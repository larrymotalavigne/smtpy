import { Routes } from '@angular/router';
import { AppLayout } from './app/layout/component/app.layout';

export const appRoutes: Routes = [
    {
        path: '',
        loadComponent: () => import('./app/pages/landing/landing').then(m => m.Landing)
    },
    {
        path: '',
        component: AppLayout,
        children: [
            { path: 'dashboard', loadComponent: () => import('./app/pages/dashboard/dashboard.component').then(m => m.DashboardComponent) },
            { path: 'domains', loadComponent: () => import('./app/pages/domains/domains.component').then(m => m.DomainsComponent) },
            { path: 'messages', loadComponent: () => import('./app/pages/messages/messages.component').then(m => m.MessagesComponent) },
            { path: 'statistics', loadComponent: () => import('./app/pages/statistics/statistics.component').then(m => m.StatisticsComponent) },
            { path: 'billing', loadComponent: () => import('./app/pages/billing/billing.component').then(m => m.BillingComponent) },
            { path: 'profile', loadComponent: () => import('./app/pages/profile/profile.component').then(m => m.ProfileComponent) },
            { path: 'settings', loadComponent: () => import('./app/pages/settings/settings.component').then(m => m.SettingsComponent) }
        ]
    },
    { path: 'auth', loadChildren: () => import('./app/pages/auth/auth.routes') },
    { path: '**', redirectTo: '/' }
];
