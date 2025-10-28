# SMTPy Quick Reference Guide

**Purpose**: Fast lookup for common tasks and patterns.

---

## 🚀 Quick Start Commands

### Development

```bash
# Backend (API)
cd back/api
uvicorn main:create_app --reload --factory

# Frontend (Angular)
cd front
npm start

# Docker (Full Stack)
make build
make run
make logs
```

### Testing

```bash
# Backend tests
cd back
pytest tests/ -v

# Frontend tests
cd front
npm test
```

---

## 📂 Where to Find Things

| What | Location |
|------|----------|
| API Routes | `back/api/views/*_view.py` |
| Business Logic | `back/api/controllers/*_controller.py` |
| Database Queries | `back/api/database/*_database.py` |
| Models | `back/api/database/models.py` |
| Frontend Components | `front/src/app/features/*/` |
| API Services | `front/src/app/core/services/` |
| Interfaces | `front/src/app/core/interfaces/` |

---

## 🔧 Common Backend Patterns

### Create New Endpoint (Full Stack)

**1. Database Layer** (`database/feature_database.py`):
```python
async def create_item(db: AsyncSession, data: dict) -> Item:
    item = Item(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def get_item(db: AsyncSession, item_id: int) -> Item | None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()
```

**2. Controller** (`controllers/feature_controller.py`):
```python
async def create_item(
    db: AsyncSession,
    data: ItemCreate,
    user_id: int
) -> Item:
    # Validation
    if await feature_database.item_exists(db, data.name):
        raise ItemExistsError()

    # Create
    item_data = {"name": data.name, "user_id": user_id}
    return await feature_database.create_item(db, item_data)
```

**3. View** (`views/feature_view.py`):
```python
@router.post("/items")
async def create_item(
    data: ItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = await feature_controller.create_item(db, data, user.id)
    return {"success": True, "data": item}
```

---

## 🎨 Common Frontend Patterns

### Create New Component

```bash
# Generate component (Angular 19)
cd front
ng generate component features/feature-name --standalone
```

**Component Structure**:
```typescript
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';

@Component({
  selector: 'app-feature',
  templateUrl: './feature.component.html',
  styleUrls: ['./feature.component.scss'],
  standalone: true,
  imports: [CommonModule, CardModule]
})
export class FeatureComponent implements OnInit {
  items: any[] = [];
  loading = false;

  ngOnInit(): void {
    this.loadItems();
  }

  loadItems(): void {
    // Load data
  }
}
```

### Add New Route

**main.ts**:
```typescript
const routes = [
  {
    path: 'feature',
    loadComponent: () => import('./app/features/feature/feature.component')
      .then(m => m.FeatureComponent)
  }
];
```

---

## 🗄️ Database Quick Reference

### Common Queries

```python
# Get all
result = await db.execute(select(Model))
items = result.scalars().all()

# Get one by ID
result = await db.execute(select(Model).where(Model.id == id))
item = result.scalar_one_or_none()

# Get with filter
result = await db.execute(
    select(Model).where(Model.user_id == user_id)
)
items = result.scalars().all()

# Get with relationships (eager loading)
result = await db.execute(
    select(Model)
    .options(selectinload(Model.related))
    .where(Model.id == id)
)
item = result.scalar_one_or_none()

# Count
result = await db.execute(select(func.count(Model.id)))
count = result.scalar()

# Create
item = Model(**data)
db.add(item)
await db.commit()
await db.refresh(item)

# Update
result = await db.execute(select(Model).where(Model.id == id))
item = result.scalar_one_or_none()
item.field = new_value
await db.commit()

# Delete
result = await db.execute(select(Model).where(Model.id == id))
item = result.scalar_one_or_none()
await db.delete(item)
await db.commit()
```

---

## 🎯 PrimeNG Components Cheatsheet

### Most Used Components

```html
<!-- Button -->
<p-button label="Click Me" icon="pi pi-check" (onClick)="handleClick()"></p-button>

<!-- Table -->
<p-table [value]="items" [paginator]="true" [rows]="10">
  <ng-template pTemplate="header">
    <tr><th>Column</th></tr>
  </ng-template>
  <ng-template pTemplate="body" let-item>
    <tr><td>{{ item.value }}</td></tr>
  </ng-template>
</p-table>

<!-- Dialog -->
<p-dialog header="Title" [(visible)]="display" [modal]="true">
  Content here
</p-dialog>

<!-- Card -->
<p-card>
  <ng-template pTemplate="header">Header</ng-template>
  <ng-template pTemplate="content">Content</ng-template>
</p-card>

<!-- Tag -->
<p-tag value="Active" severity="success"></p-tag>

<!-- Chart -->
<p-chart type="line" [data]="chartData" [options]="options"></p-chart>

<!-- Toast (notification) -->
<p-toast position="top-right"></p-toast>
<!-- Trigger in component -->
this.messageService.add({
  severity: 'success',
  summary: 'Success',
  detail: 'Operation completed'
});
```

---

## 🎨 Tailwind CSS Common Classes

### Layout
```html
<!-- Flex -->
<div class="flex justify-between items-center gap-4">

<!-- Grid -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">

<!-- Container -->
<div class="container mx-auto px-4">
```

### Typography
```html
<h1 class="text-3xl font-bold text-gray-900">
<p class="text-sm text-gray-600">
```

### Spacing
```html
<div class="p-4 m-2">         <!-- Padding & Margin -->
<div class="mt-4 mb-2">        <!-- Margin top/bottom -->
<div class="px-6 py-4">        <!-- Padding x/y axis -->
```

### Colors
```html
<div class="bg-blue-600 text-white">
<div class="border border-gray-300">
```

### Responsive
```html
<div class="w-full md:w-1/2 lg:w-1/3">
<div class="hidden md:block">  <!-- Show on md and up -->
```

---

## 🔐 Authentication Patterns

### Backend - Protect Route

```python
from dependencies import get_current_user

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"user": current_user.username}
```

### Frontend - Auth Guard

```typescript
export const authGuard = () => {
  const authService = inject(AuthService);
  if (authService.isAuthenticated()) {
    return true;
  }
  return inject(Router).navigate(['/login']);
};

// In routes
{
  path: 'protected',
  canActivate: [authGuard],
  loadComponent: () => import('./protected.component')
}
```

---

## 🐛 Debugging Tips

### Backend

```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing item: {item_id}")

# Print SQL queries
# In database/session.py
engine = create_async_engine(
    database_url,
    echo=True  # Prints all SQL
)

# Debug session
from sqlalchemy import inspect
inspector = inspect(db)
print(inspector.get_table_names())
```

### Frontend

```typescript
// Console logging
console.log('Data:', this.items);
console.table(this.items);  // Nice table view

// RxJS debugging
import { tap } from 'rxjs/operators';

this.api.getItems()
  .pipe(
    tap(data => console.log('API Response:', data))
  )
  .subscribe();

// Angular DevTools
// Install Chrome extension for component inspection
```

---

## 📦 Dependency Injection

### Backend (FastAPI)

```python
# Define dependency
async def get_current_user(
    session: dict = Depends(get_session),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Get user from session
    ...

# Use in endpoint
@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return user
```

### Frontend (Angular)

```typescript
// Service injection
constructor(
  private http: HttpClient,
  private router: Router,
  private messageService: MessageService
) {}

// Optional dependencies
constructor(
  @Optional() private config: Config
) {}
```

---

## 🔄 Common RxJS Patterns

```typescript
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';

export class Component implements OnDestroy {
  private destroy$ = new Subject<void>();

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Auto-unsubscribe
  loadData(): void {
    this.api.getData()
      .pipe(takeUntil(this.destroy$))
      .subscribe(data => this.data = data);
  }

  // Search with debounce
  searchControl.valueChanges
    .pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    )
    .subscribe(term => this.search(term));
}
```

---

## 🎯 Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+psycopg://user:pass@localhost/smtpy
SMTPY_DB_PATH=/path/to/dev.db

# API
SECRET_KEY=your-secret-key-here
DEBUG=true

# Stripe
STRIPE_API_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# SMTP
SMTP_HOST=localhost
SMTP_PORT=1025
```

### Frontend (environment.ts)

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

---

## 🧪 Testing Snippets

### Backend Test

```python
def test_create_domain(client):
    response = client.post("/api/domains", json={
        "name": "example.com"
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Frontend Test

```typescript
it('should load domains', () => {
  component.loadDomains();
  expect(component.loading).toBe(true);
  // Add more assertions
});
```

---

## 📊 Common Errors & Solutions

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'x'` | Run `uv sync` to install deps |
| `Cannot find module '@angular/...'` | Run `npm install` |
| `Database locked` (SQLite) | Check for open connections, restart app |
| `Port 8000 already in use` | Kill process: `lsof -ti:8000 \| xargs kill -9` |
| `CORS error` | Add domain to CORS middleware |
| `401 Unauthorized` | Check session/token in request |

---

## 🔗 Important URLs (Development)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:4200 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| SMTP Server | localhost:1025 |

---

## 📝 Git Workflow

```bash
# Feature branch
git checkout -b feature/new-feature

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/new-feature

# Create PR, merge, then:
git checkout main
git pull origin main
```

---

**Last Updated**: October 19, 2025
**Version**: 1.0
