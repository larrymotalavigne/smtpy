# SMTPy Frontend Development Guide

**Purpose**: Quick reference for Angular frontend development in SMTPy.

---

## 🎨 Frontend Tech Stack (Updated Oct 2025)

### Core Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Angular** | 19.2.15 | Web framework |
| **PrimeNG** | 19.1.4 | UI component library |
| **@primeuix/themes** | 1.2.5 | PrimeNG theming system |
| **Tailwind CSS** | 4.1.14 | Utility-first CSS |
| **@tailwindcss/postcss** | 4.1.14 | PostCSS plugin for Tailwind v4 |
| **TypeScript** | 5.7.0 | Type safety |
| **RxJS** | 7.8.2 | Reactive programming |
| **Chart.js** | 4.5.1 | Charts and graphs |

### Configuration Files

```
front/
├── package.json              # Dependencies
├── angular.json             # Angular CLI config
├── tsconfig.json            # TypeScript config (moduleResolution: "bundler")
├── postcss.config.js        # Tailwind v4 PostCSS config
├── src/
│   ├── main.ts              # App bootstrap with PrimeNG config
│   ├── styles.scss          # Global styles with Tailwind v4
│   └── environments/        # Environment configs
```

---

## 📁 Frontend Project Structure

```
front/src/app/
├── core/                           # Core functionality
│   ├── interfaces/                 # TypeScript interfaces
│   │   ├── domain.interface.ts
│   │   ├── message.interface.ts
│   │   ├── billing.interface.ts
│   │   └── common.interface.ts
│   ├── services/                   # API services
│   │   ├── auth.service.ts
│   │   ├── domains-api.service.ts
│   │   ├── messages-api.service.ts
│   │   └── billing-api.service.ts
│   └── interceptors/               # HTTP interceptors
│       ├── auth.interceptor.ts
│       └── error.interceptor.ts
├── features/                       # Feature modules (standalone components)
│   ├── landing/                    # ✅ COMPLETED
│   │   ├── landing.component.ts
│   │   ├── landing.component.html
│   │   └── landing.component.scss
│   ├── dashboard/                  # ✅ COMPLETED
│   │   ├── dashboard.component.ts
│   │   ├── dashboard.component.html
│   │   └── dashboard.component.scss
│   ├── domains/                    # ⏳ NEEDS REDESIGN
│   │   ├── domains.component.ts
│   │   ├── domains.component.html
│   │   └── domains.component.scss
│   ├── messages/                   # ⏳ NEEDS REDESIGN
│   │   ├── messages.component.ts
│   │   ├── messages.component.html
│   │   └── messages.component.scss
│   ├── billing/                    # ⏳ NEEDS UI REDESIGN
│   │   ├── billing.component.ts    # (logic exists)
│   │   ├── billing.component.html
│   │   └── billing.component.scss
│   └── statistics/                 # ⏳ NEEDS IMPLEMENTATION
│       ├── statistics.component.ts
│       ├── statistics.component.html
│       └── statistics.component.scss
├── shared/                         # Shared components
│   ├── components/
│   │   └── layout/
│   │       ├── main-layout.component.ts    # Standalone
│   │       ├── main-layout.component.html
│   │       └── main-layout.component.scss
│   └── shared.module.ts           # Shared module (no components)
└── app.component.ts               # Root component
```

---

## 🔧 Configuration Details

### Tailwind CSS v4 Setup

**postcss.config.js**:
```javascript
module.exports = {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};
```

**styles.scss**:
```scss
/* Tailwind CSS v4 - Simplified import */
@import "tailwindcss";

/* PrimeIcons */
@import "primeicons/primeicons.css";

/* Custom theme configuration */
@theme {
  /* Custom colors */
  --color-primary-500: #2196f3;
  --color-secondary-500: #9c27b0;
  /* ... more theme variables */
}
```

### PrimeNG v19 Setup

**main.ts**:
```typescript
import { providePrimeNG } from 'primeng/config';

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
    provideAnimations(),
    providePrimeNG({
      ripple: true
    }),
    MessageService,
    ConfirmationService
  ]
});
```

### TypeScript Configuration

**tsconfig.json** (Key settings):
```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",  // Required for Angular 19
    "target": "ES2022",
    "module": "ES2022",
    "strict": true
  }
}
```

---

## 🧩 Component Patterns

### Standalone Components (Angular 19 Standard)

**✅ CORRECT Pattern**:
```typescript
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-feature',
  templateUrl: './feature.component.html',
  styleUrls: ['./feature.component.scss'],
  standalone: true,  // Standalone component
  imports: [
    CommonModule,
    CardModule,
    ButtonModule
  ]
})
export class FeatureComponent {
  // Component logic
}
```

### Service Integration

**API Service Pattern**:
```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiResponse, DomainResponse } from '../interfaces/domain.interface';

@Injectable({
  providedIn: 'root'
})
export class DomainsApiService {
  private apiUrl = '/api/domains';

  constructor(private http: HttpClient) {}

  getDomains(): Observable<ApiResponse<DomainResponse[]>> {
    return this.http.get<ApiResponse<DomainResponse[]>>(this.apiUrl);
  }

  createDomain(data: DomainCreate): Observable<ApiResponse<DomainResponse>> {
    return this.http.post<ApiResponse<DomainResponse>>(this.apiUrl, data);
  }
}
```

### Component with Service

**Component Pattern**:
```typescript
import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { DomainsApiService } from '../../core/services/domains-api.service';

@Component({
  selector: 'app-domains',
  templateUrl: './domains.component.html',
  standalone: true,
  imports: [/* ... */]
})
export class DomainsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  domains: DomainResponse[] = [];
  loading = false;

  constructor(private domainsApi: DomainsApiService) {}

  ngOnInit(): void {
    this.loadDomains();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDomains(): void {
    this.loading = true;
    this.domainsApi.getDomains()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response.success) {
            this.domains = response.data || [];
          }
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading domains:', error);
          this.loading = false;
        }
      });
  }
}
```

---

## 🎨 PrimeNG Component Usage

### Common PrimeNG Components

```typescript
// Table with filtering and pagination
import { TableModule } from 'primeng/table';

<p-table
  [value]="domains"
  [paginator]="true"
  [rows]="10"
  [showCurrentPageReport]="true"
  [loading]="loading"
  class="p-datatable-sm">
  <ng-template pTemplate="header">
    <tr>
      <th>Domain</th>
      <th>Status</th>
      <th>Actions</th>
    </tr>
  </ng-template>
  <ng-template pTemplate="body" let-domain>
    <tr>
      <td>{{ domain.name }}</td>
      <td><p-tag [value]="domain.status" [severity]="getStatusSeverity(domain.status)"></p-tag></td>
      <td>
        <p-button icon="pi pi-pencil" [text]="true"></p-button>
      </td>
    </tr>
  </ng-template>
</p-table>

// Dialog
import { DialogModule } from 'primeng/dialog';

<p-dialog
  header="Add Domain"
  [(visible)]="displayDialog"
  [modal]="true"
  [style]="{width: '500px'}">
  <!-- Dialog content -->
</p-dialog>

// Cards
import { CardModule } from 'primeng/card';

<p-card>
  <ng-template pTemplate="header">
    <h3>Card Title</h3>
  </ng-template>
  <ng-template pTemplate="content">
    <p>Card content</p>
  </ng-template>
</p-card>

// Charts
import { ChartModule } from 'primeng/chart';

<p-chart type="line" [data]="chartData" [options]="chartOptions"></p-chart>
```

---

## 🎯 Styling Patterns

### Using Tailwind CSS v4

```html
<!-- Utility classes -->
<div class="flex justify-between items-center p-4 bg-white rounded-lg shadow">
  <h2 class="text-2xl font-bold text-gray-900">Title</h2>
  <button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
    Action
  </button>
</div>

<!-- Responsive -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  <!-- Grid items -->
</div>
```

### Component-Specific SCSS

```scss
// feature.component.scss
.feature-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.feature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

// Using ::ng-deep for PrimeNG overrides
::ng-deep .p-card {
  border-radius: 12px;
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-4px);
  }
}

// Responsive
@media (max-width: 768px) {
  .feature-container {
    padding: 1rem;
  }
}
```

---

## 🔄 Routing Configuration

### Lazy Loading (Current Setup)

**main.ts**:
```typescript
const routes = [
  {
    path: '',
    loadComponent: () => import('./app/features/landing/landing.component')
      .then(m => m.LandingComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./app/features/dashboard/dashboard.component')
      .then(m => m.DashboardComponent)
  },
  {
    path: 'domains',
    loadComponent: () => import('./app/features/domains/domains.component')
      .then(m => m.DomainsComponent)
  }
  // ... more routes
];
```

### Auth Guards (To be implemented)

```typescript
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  router.navigate(['/login']);
  return false;
};

// Usage in routes
{
  path: 'dashboard',
  loadComponent: () => import('./features/dashboard/dashboard.component')
    .then(m => m.DashboardComponent),
  canActivate: [authGuard]
}
```

---

## 📊 State Management Patterns

### Component State (Simple)

```typescript
export class FeatureComponent {
  // Loading states
  loading = false;
  saving = false;

  // Data
  items: Item[] = [];
  selectedItem: Item | null = null;

  // UI states
  displayDialog = false;
  activeTab = 0;
}
```

### RxJS State (Medium Complexity)

```typescript
import { BehaviorSubject, Observable } from 'rxjs';

export class FeatureComponent {
  private itemsSubject = new BehaviorSubject<Item[]>([]);
  items$ = this.itemsSubject.asObservable();

  private loadingSubject = new BehaviorSubject<boolean>(false);
  loading$ = this.loadingSubject.asObservable();

  loadItems(): void {
    this.loadingSubject.next(true);
    this.apiService.getItems()
      .subscribe({
        next: (items) => {
          this.itemsSubject.next(items);
          this.loadingSubject.next(false);
        }
      });
  }
}
```

---

## 🧪 Testing Patterns

### Component Testing

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FeatureComponent } from './feature.component';

describe('FeatureComponent', () => {
  let component: FeatureComponent;
  let fixture: ComponentFixture<FeatureComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FeatureComponent]  // Standalone component
    }).compileComponents();

    fixture = TestBed.createComponent(FeatureComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
```

---

## 🎨 Design System

### Color Palette

```scss
// Primary colors (Blue)
--color-primary-50: #e3f2fd;
--color-primary-500: #2196f3;  // Main brand color
--color-primary-900: #0d47a1;

// Secondary colors (Purple)
--color-secondary-50: #f3e5f5;
--color-secondary-500: #9c27b0;
--color-secondary-900: #4a148c;

// Semantic colors
--color-success: #10b981;
--color-warning: #f59e0b;
--color-danger: #ef4444;
--color-info: #3b82f6;
```

### Typography

```scss
// Font sizes (using clamp for responsive)
--font-size-xs: 0.75rem;      // 12px
--font-size-sm: 0.875rem;     // 14px
--font-size-base: 1rem;       // 16px
--font-size-lg: 1.125rem;     // 18px
--font-size-xl: 1.25rem;      // 20px
--font-size-2xl: 1.5rem;      // 24px
--font-size-3xl: clamp(2rem, 4vw, 2.5rem);
```

### Spacing Scale

```scss
--spacing-1: 0.25rem;  // 4px
--spacing-2: 0.5rem;   // 8px
--spacing-3: 0.75rem;  // 12px
--spacing-4: 1rem;     // 16px
--spacing-6: 1.5rem;   // 24px
--spacing-8: 2rem;     // 32px
```

---

## 🚀 Build & Development

### Development Server

```bash
npm start
# Runs on http://localhost:4200
```

### Production Build

```bash
npm run build
# Output: dist/smtpy-frontend/
```

### Common Commands

```bash
# Install dependencies
npm install

# Run tests
npm test

# Lint code
npm run lint

# Check for outdated packages
npm outdated
```

---

## 📝 Code Style Guidelines

### TypeScript Style

```typescript
// ✅ CORRECT - Explicit types
export interface Domain {
  id: number;
  name: string;
  verified: boolean;
}

// ✅ CORRECT - Async/await
async loadDomains(): Promise<void> {
  try {
    const response = await firstValueFrom(this.api.getDomains());
    this.domains = response.data;
  } catch (error) {
    console.error('Error:', error);
  }
}

// ❌ AVOID - Implicit any
loadDomains() {  // Missing return type
  this.api.getDomains().subscribe((data) => {  // data is 'any'
    this.domains = data;
  });
}
```

### Template Style

```html
<!-- ✅ CORRECT - Clear structure -->
<div class="container">
  <header class="header">
    <h1>{{ title }}</h1>
  </header>

  <main class="content">
    <p-table [value]="items" [loading]="loading">
      <!-- Table content -->
    </p-table>
  </main>
</div>

<!-- ❌ AVOID - Inline styles -->
<div style="padding: 20px;">
  <h1 style="color: blue;">{{ title }}</h1>
</div>
```

---

## 🔗 Useful Resources

- [Angular 19 Docs](https://angular.dev)
- [PrimeNG 19 Docs](https://primeng.org)
- [Tailwind CSS v4 Docs](https://tailwindcss.com/docs)
- [RxJS Docs](https://rxjs.dev)

---

**Last Updated**: October 19, 2025
**Version**: 1.0
