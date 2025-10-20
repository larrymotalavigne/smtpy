import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { filter } from 'rxjs/operators';
import { AuthService, User } from '../../../core/services/auth.service';

// PrimeNG Modules
import { ButtonModule } from 'primeng/button';
import { MenuModule } from 'primeng/menu';
import { SidebarModule } from 'primeng/sidebar';
import { AvatarModule } from 'primeng/avatar';
import { RippleModule } from 'primeng/ripple';
import { ToastModule } from 'primeng/toast';

@Component({
  selector: 'app-main-layout',
  templateUrl: './main-layout.component.html',
  styleUrls: ['./main-layout.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ButtonModule,
    MenuModule,
    SidebarModule,
    AvatarModule,
    RippleModule,
    ToastModule
  ]
})
export class MainLayoutComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  sidebarVisible = false;
  currentUser: User | null = null;
  currentRoute = '';

  menuItems = [
    {
      label: 'Dashboard',
      icon: 'pi pi-home',
      routerLink: '/dashboard'
    },
    {
      label: 'Domains',
      icon: 'pi pi-globe',
      routerLink: '/domains'
    },
    {
      label: 'Messages',
      icon: 'pi pi-envelope',
      routerLink: '/messages'
    },
    {
      label: 'Billing',
      icon: 'pi pi-credit-card',
      routerLink: '/billing'
    }
  ];

  userMenuItems = [
    {
      label: 'Profile',
      icon: 'pi pi-user',
      command: () => this.navigateToProfile()
    },
    {
      label: 'Settings',
      icon: 'pi pi-cog',
      command: () => this.navigateToSettings()
    },
    {
      separator: true
    },
    {
      label: 'Logout',
      icon: 'pi pi-sign-out',
      command: () => this.logout()
    }
  ];

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Subscribe to current user
    this.authService.currentUser$
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        this.currentUser = user;
      });

    // Track current route for active menu highlighting
    this.router.events
      .pipe(
        filter(event => event instanceof NavigationEnd),
        takeUntil(this.destroy$)
      )
      .subscribe((event) => {
        this.currentRoute = (event as NavigationEnd).urlAfterRedirects;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  toggleSidebar(): void {
    this.sidebarVisible = !this.sidebarVisible;
  }

  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }

  navigateToSettings(): void {
    this.router.navigate(['/settings']);
  }

  logout(): void {
    this.authService.logout().subscribe(() => {
      this.router.navigate(['/auth/login']);
    });
  }

  isRouteActive(routerLink: string): boolean {
    return this.currentRoute.startsWith(routerLink);
  }

  getUserInitials(): string {
    if (!this.currentUser) return '';
    const name = this.currentUser.username || this.currentUser.email;
    return name.substring(0, 2).toUpperCase();
  }

  getUserDisplayName(): string {
    if (!this.currentUser) return '';
    return this.currentUser.username || this.currentUser.email;
  }
}