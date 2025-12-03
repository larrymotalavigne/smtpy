import {Routes} from '@angular/router';
import {adminGuard, authGuard} from '@/core/guards/auth.guard';

export const appRoutes: Routes = [
    {
        path: '',
        loadComponent: () => import('./app/pages/landing/landing').then(m => m.Landing)
    },
    {
        path: '',
        loadComponent: () => import('./app/layout/component/app.layout').then(m => m.AppLayout),
        children: [
            {path: 'dashboard', loadComponent: () => import('./app/pages/dashboard/dashboard.component').then(m => m.DashboardComponent)},
            {
                path: 'admin',
                loadComponent: () => import('./app/pages/admin/admin.component').then(m => m.AdminComponent),
                canActivate: [adminGuard]
            },
            {path: 'domains', loadComponent: () => import('./app/pages/domains/domains.component').then(m => m.DomainsComponent)},
            {path: 'aliases', loadComponent: () => import('./app/pages/aliases/aliases.component').then(m => m.AliasesComponent)},
            {path: 'messages', loadComponent: () => import('./app/pages/messages/messages.component').then(m => m.MessagesComponent)},
            {
                path: 'statistics',
                loadComponent: () => import('./app/pages/statistics/statistics.component').then(m => m.StatisticsComponent)
            },
            {path: 'billing', loadComponent: () => import('./app/pages/billing/billing.component').then(m => m.BillingComponent)},
            {path: 'profile', loadComponent: () => import('./app/pages/profile/profile.component').then(m => m.ProfileComponent)},
            {path: 'settings', loadComponent: () => import('./app/pages/settings/settings.component').then(m => m.SettingsComponent)}
        ]
    },
    {path: 'auth', loadChildren: () => import('./app/pages/auth/auth.routes')},
    {path: '**', redirectTo: '/'}
];
