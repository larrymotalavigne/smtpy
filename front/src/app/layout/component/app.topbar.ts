import {Component, OnInit} from '@angular/core';
import {MenuItem} from 'primeng/api';
import {Router, RouterModule} from '@angular/router';
import {CommonModule} from '@angular/common';
import {StyleClassModule} from 'primeng/styleclass';
import {AppConfigurator} from './app.configurator';
import {LayoutService} from '../../core/services/layout.service';
import {AuthService} from '@/core/services/auth.service';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [RouterModule, CommonModule, StyleClassModule, AppConfigurator],
    template: `
        <div class="layout-topbar">
            <div class="layout-topbar-logo-container">
                <button class="layout-menu-button layout-topbar-action" (click)="layoutService.onMenuToggle()">
                    <i class="pi pi-bars"></i>
                </button>
                <a class="layout-topbar-logo" routerLink="/dashboard">
                    <i class="pi pi-envelope" style="font-size: 2rem; color: var(--primary-color);"></i>
                    <span>SMTPy</span>
                </a>
            </div>

            <div class="layout-topbar-actions">
                <div class="layout-config-menu">
                    <button type="button" class="layout-topbar-action" (click)="toggleDarkMode()">
                        <i [ngClass]="{ 'pi': true, 'pi-moon': layoutService.isDarkTheme(), 'pi-sun': !layoutService.isDarkTheme() }"></i>
                    </button>
                    <div class="relative">
                        <button
                            class="layout-topbar-action layout-topbar-action-highlight"
                            pStyleClass="@next"
                            enterFromClass="hidden"
                            enterActiveClass="animate-scalein"
                            leaveToClass="hidden"
                            leaveActiveClass="animate-fadeout"
                            [hideOnOutsideClick]="true"
                        >
                            <i class="pi pi-palette"></i>
                        </button>
                        <app-configurator/>
                    </div>
                </div>

                <button class="layout-topbar-menu-button layout-topbar-action" pStyleClass="@next" enterFromClass="hidden"
                        enterActiveClass="animate-scalein" leaveToClass="hidden" leaveActiveClass="animate-fadeout"
                        [hideOnOutsideClick]="true">
                    <i class="pi pi-ellipsis-v"></i>
                </button>

                <div class="layout-topbar-menu hidden lg:block">
                    <div class="layout-topbar-menu-content">
                        <button type="button" class="layout-topbar-action" routerLink="/profile">
                            <i class="pi pi-user"></i>
                            <span>{{ currentUser?.username || 'Profil' }}</span>
                        </button>
                        <button type="button" class="layout-topbar-action" (click)="logout()">
                            <i class="pi pi-sign-out"></i>
                            <span>Déconnexion</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>`
})
export class AppTopbar implements OnInit {
    items!: MenuItem[];
    currentUser: any = null;

    constructor(
        public layoutService: LayoutService,
        private authService: AuthService,
        private router: Router
    ) {
    }

    ngOnInit() {
        this.authService.currentUser$.subscribe(user => {
            this.currentUser = user;
        });
    }

    toggleDarkMode() {
        this.layoutService.layoutConfig.update((state) => ({...state, darkTheme: !state.darkTheme}));
    }

    logout() {
        this.authService.logout().subscribe({
            next: () => {
                this.router.navigate(['/auth/login']);
            },
            error: () => {
                this.router.navigate(['/auth/login']);
            }
        });
    }
}
