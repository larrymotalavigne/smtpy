# SMTPy Architecture Reference

**Purpose**: Quick reference for understanding the SMTPy architecture and development patterns.

---

## 📐 Architecture Principles

### 3-Layer Architecture (Strict Separation)

```
┌─────────────────────────────────────────────┐
│              Views Layer                     │
│  (*_view.py in views/ directory)            │
│  - FastAPI routers & request handling       │
│  - Dependency injection                     │
│  - No business logic                        │
└─────────────────┬───────────────────────────┘
                  │ calls
                  ▼
┌─────────────────────────────────────────────┐
│           Controllers Layer                  │
│  (*_controller.py in controllers/)          │
│  - Pure Python business logic               │
│  - No FastAPI imports                       │
│  - Accept explicit dependencies             │
└─────────────────┬───────────────────────────┘
                  │ calls
                  ▼
┌─────────────────────────────────────────────┐
│            Database Layer                    │
│  (*_database.py in database/)               │
│  - Pure SQLAlchemy async queries            │
│  - AsyncSession as first argument           │
│  - No business logic                        │
└─────────────────────────────────────────────┘
```

### Layer Responsibilities

#### Views Layer (`*_view.py`)
**Location**: `back/api/views/`
**Purpose**: HTTP interface and routing
**Allowed**:
- FastAPI routers, routes, dependencies
- Request/response models (Pydantic)
- Dependency injection (`Depends()`)
- Calling controllers
- HTTP status codes and responses

**Not Allowed**:
- Business logic
- Direct database queries
- Complex data transformations

**Example**:
```python
# domains_view.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from controllers import domains_controller

router = APIRouter()

@router.post("/domains")
async def create_domain(
    domain_data: DomainCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await domains_controller.create_domain(
        db=db,
        domain_data=domain_data
    )
    return {"success": True, "data": result}
```

#### Controllers Layer (`*_controller.py`)
**Location**: `back/api/controllers/`
**Purpose**: Business logic orchestration
**Allowed**:
- Pure Python business logic
- Orchestrating multiple database calls
- Data validation and transformation
- Calling external services
- Raising business exceptions

**Not Allowed**:
- FastAPI imports or HTTP concepts
- Direct database session management
- Creating database sessions

**Example**:
```python
# domains_controller.py
from sqlalchemy.ext.asyncio import AsyncSession
from database import domains_database

async def create_domain(
    db: AsyncSession,
    domain_data: DomainCreate,
    user_id: int
) -> Domain:
    # Business logic
    if await domains_database.domain_exists(db, domain_data.name):
        raise DomainAlreadyExistsError()

    # Create domain
    domain = await domains_database.create_domain(
        db, domain_data, user_id
    )

    # Generate DNS records
    await domains_database.create_dns_records(db, domain.id)

    return domain
```

#### Database Layer (`*_database.py`)
**Location**: `back/api/database/`
**Purpose**: Data access and persistence
**Allowed**:
- SQLAlchemy queries
- AsyncSession operations
- Model CRUD operations
- Query optimization

**Not Allowed**:
- Business logic
- Creating sessions (receive as parameter)
- HTTP concepts

**Example**:
```python
# domains_database.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def create_domain(
    db: AsyncSession,
    domain_data: DomainCreate,
    user_id: int
) -> Domain:
    domain = Domain(
        name=domain_data.name,
        user_id=user_id,
        verified=False
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return domain

async def domain_exists(
    db: AsyncSession,
    domain_name: str
) -> bool:
    result = await db.execute(
        select(Domain).where(Domain.name == domain_name)
    )
    return result.scalar_one_or_none() is not None
```

---

## 🏗️ Project Structure

```
smtpy/
├── back/
│   ├── api/                        # FastAPI application
│   │   ├── core/                   # Core configuration
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   ├── database.py        # Database connection
│   │   │   └── middlewares.py     # Custom middleware
│   │   ├── views/                  # API routers (*_view.py)
│   │   │   ├── domains_view.py
│   │   │   ├── messages_view.py
│   │   │   ├── billing_view.py
│   │   │   └── subscriptions_view.py
│   │   ├── controllers/            # Business logic (*_controller.py)
│   │   │   ├── domains_controller.py
│   │   │   ├── messages_controller.py
│   │   │   └── billing_controller.py
│   │   ├── database/               # Data access (*_database.py)
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── domains_database.py
│   │   │   ├── messages_database.py
│   │   │   └── billing_database.py
│   │   ├── services/               # External services
│   │   │   ├── stripe_service.py
│   │   │   └── email_service.py
│   │   ├── static/                 # Static files
│   │   └── main.py                 # App factory
│   ├── smtp/                       # SMTP server
│   │   ├── smtp_server/
│   │   ├── forwarding/
│   │   └── config_dns/
│   └── tests/                      # Test suite
├── front/                          # Angular frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/              # Core services & interfaces
│   │   │   ├── features/          # Feature modules
│   │   │   └── shared/            # Shared components
│   │   └── environments/
│   └── package.json
└── docs/                           # Documentation
    ├── tasks.md                    # Current tasks
    └── features/                   # Feature specs
```

---

## 🔄 Data Flow Patterns

### Request Flow (Typical)

```
HTTP Request
    ↓
View Layer (domains_view.py)
    ↓ (dependency injection)
Database Session (get_db)
    ↓ (pass to controller)
Controller Layer (domains_controller.py)
    ↓ (business logic)
Database Layer (domains_database.py)
    ↓ (query execution)
Database (PostgreSQL/SQLite)
    ↓ (results)
Controller (transform/validate)
    ↓ (return data)
View (format response)
    ↓
HTTP Response
```

### Example: Creating a Domain

```python
# 1. View receives request
@router.post("/domains")
async def create_domain(
    domain_data: DomainCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    # 2. View calls controller
    result = await domains_controller.create_domain(
        db=db,
        domain_data=domain_data,
        user_id=user_id
    )
    # 5. View formats response
    return {"success": True, "data": result}

# 3. Controller orchestrates
async def create_domain(db, domain_data, user_id):
    # Validation
    if await domains_database.domain_exists(db, domain_data.name):
        raise DomainExistsError()

    # 4. Controller calls database
    domain = await domains_database.create_domain(db, domain_data, user_id)
    await domains_database.create_dns_records(db, domain.id)

    return domain

# Database performs queries
async def create_domain(db, domain_data, user_id):
    domain = Domain(name=domain_data.name, user_id=user_id)
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return domain
```

---

## 📦 Module Dependencies

### Dependency Rules

1. **Views** can import:
   - FastAPI modules
   - Controllers
   - Pydantic models
   - Dependencies (get_db, get_current_user)

2. **Controllers** can import:
   - Database modules
   - Services
   - Models (for type hints)
   - Utility functions
   - **CANNOT import FastAPI**

3. **Database** can import:
   - SQLAlchemy
   - Models
   - **CANNOT import FastAPI or Controllers**

### Import Examples

```python
# ✅ CORRECT - View
from fastapi import APIRouter, Depends
from controllers import domains_controller
from database.session import get_db

# ✅ CORRECT - Controller
from database import domains_database
from services.email_service import send_verification_email

# ✅ CORRECT - Database
from sqlalchemy import select
from database.models import Domain

# ❌ WRONG - Controller importing FastAPI
from fastapi import HTTPException  # NO!

# ❌ WRONG - Database importing Controller
from controllers import domains_controller  # NO!
```

---

## 🎯 Code Style Guidelines

### Function-Based vs Class-Based

**✅ PREFERRED - Function-based**:
```python
# Controller
async def create_domain(db: AsyncSession, domain_data: DomainCreate):
    domain = await domains_database.create_domain(db, domain_data)
    return domain

# Database
async def get_domain(db: AsyncSession, domain_id: int):
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id)
    )
    return result.scalar_one_or_none()
```

**❌ AVOID - Class-based**:
```python
# Don't do this for business logic
class DomainController:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_domain(self, domain_data: DomainCreate):
        ...
```

### Import Aliases

**✅ CORRECT - No aliases**:
```python
from database import domains_database
from controllers import domains_controller

result = await domains_database.get_domain(db, domain_id)
```

**❌ WRONG - Using aliases**:
```python
from database import domains_database as dd  # NO!
from controllers import domains_controller as dc  # NO!
```

### Explicit Dependencies

**✅ CORRECT - Explicit parameters**:
```python
async def create_domain(
    db: AsyncSession,
    domain_data: DomainCreate,
    user_id: int,
    email_service: EmailService
):
    # All dependencies are explicit
    ...
```

**❌ WRONG - Hidden dependencies**:
```python
async def create_domain(domain_data: DomainCreate):
    # Where does db come from? Where is user_id?
    db = get_db()  # Hidden dependency!
    ...
```

---

## 🗄️ Database Patterns

### Session Management

**✅ CORRECT - Dependency injection**:
```python
# View
@router.get("/domains")
async def list_domains(db: AsyncSession = Depends(get_db)):
    domains = await domains_controller.list_domains(db)
    return domains
```

**❌ WRONG - Creating sessions**:
```python
# Controller
async def list_domains():
    async with get_db() as db:  # NO! Don't create sessions
        ...
```

### Async Queries

**✅ CORRECT - Using async/await**:
```python
async def get_domain(db: AsyncSession, domain_id: int):
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id)
    )
    return result.scalar_one_or_none()
```

### Eager Loading

**✅ CORRECT - Using selectinload**:
```python
from sqlalchemy.orm import selectinload

async def get_domain_with_aliases(db: AsyncSession, domain_id: int):
    result = await db.execute(
        select(Domain)
        .options(selectinload(Domain.aliases))
        .where(Domain.id == domain_id)
    )
    return result.scalar_one_or_none()
```

---

## 🔐 Security Patterns

### Authentication

```python
# Dependency for getting current user
async def get_current_user(
    session: str = Depends(get_session),
    db: AsyncSession = Depends(get_db)
) -> User:
    user_id = session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401)

    user = await user_database.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=401)

    return user
```

### Authorization

```python
# View with auth check
@router.delete("/domains/{domain_id}")
async def delete_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Controller handles ownership check
    await domains_controller.delete_domain(
        db=db,
        domain_id=domain_id,
        user_id=current_user.id
    )
```

---

## 🧪 Testing Patterns

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_create_domain(client):
    # Test uses in-memory database automatically
    response = client.post("/domains", json={
        "name": "example.com"
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
```

---

## 📝 File Naming Conventions

| Type | Location | Pattern | Example |
|------|----------|---------|---------|
| View | `views/` | `*_view.py` | `domains_view.py` |
| Controller | `controllers/` | `*_controller.py` | `domains_controller.py` |
| Database | `database/` | `*_database.py` | `domains_database.py` |
| Model | `database/` | `models.py` | `models.py` |
| Service | `services/` | `*_service.py` | `stripe_service.py` |
| Test | `tests/` | `test_*.py` | `test_domains.py` |

---

## 🚀 Common Patterns

### Creating a New Feature

1. **Create Database Layer** (`database/feature_database.py`)
   ```python
   async def create_feature(db: AsyncSession, data: FeatureCreate):
       feature = Feature(**data.dict())
       db.add(feature)
       await db.commit()
       await db.refresh(feature)
       return feature
   ```

2. **Create Controller** (`controllers/feature_controller.py`)
   ```python
   async def create_feature(db: AsyncSession, data: FeatureCreate, user_id: int):
       # Validation
       if await feature_database.exists(db, data.name):
           raise FeatureExistsError()

       # Create
       feature = await feature_database.create_feature(db, data)
       return feature
   ```

3. **Create View** (`views/feature_view.py`)
   ```python
   @router.post("/features")
   async def create_feature(
       data: FeatureCreate,
       db: AsyncSession = Depends(get_db),
       user: User = Depends(get_current_user)
   ):
       result = await feature_controller.create_feature(db, data, user.id)
       return {"success": True, "data": result}
   ```

---

**Last Updated**: October 19, 2025
**Version**: 1.0
