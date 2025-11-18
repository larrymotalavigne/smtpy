# Project Recreation Prompt: Email SaaS Platform

Use this prompt to create a similar email management SaaS platform with production-ready infrastructure.

---

## 🎯 PROJECT OVERVIEW

Create a production-ready SaaS platform for email management with the following characteristics:

**Core Functionality:**
- Email aliasing and forwarding service
- Domain management with DNS verification
- Real-time message tracking and analytics
- Subscription-based billing with Stripe integration
- Multi-tenant architecture with user organizations
- Admin panel for system management

**Architecture Philosophy:**
- Microservices architecture (API + SMTP server)
- Async-first design for high performance
- Clean 3-layer architecture (Views → Controllers → Database)
- Containerized deployment with Docker
- CI/CD automation with GitHub Actions
- Production deployment on self-hosted infrastructure

---

## 🛠️ TECHNOLOGY STACK

### Backend Stack

**Core Framework & Runtime:**
- Python 3.14+ (latest stable version)
- FastAPI 0.104+ (async web framework)
- Uvicorn with standard extras (ASGI server)
- SQLAlchemy v2 with async support (ORM)

**Email Processing:**
- aiosmtpd (async SMTP server for receiving emails)
- aiosmtplib (async SMTP client for sending emails)
- dkimpy (DKIM signing for email authentication)
- dnspython (DNS operations and verification)

**Security & Authentication:**
- passlib[bcrypt] (password hashing)
- itsdangerous (secure token generation)
- cryptography (cryptographic operations)
- Session-based authentication (no JWT)

**Database:**
- PostgreSQL 18 with async driver (production)
- psycopg[binary, pool] (connection pooling)
- aiosqlite (SQLite for development)
- Alembic (database migrations)

**Payment Integration:**
- Stripe SDK (subscription billing and webhooks)

**Data Validation & Config:**
- Pydantic v2 with email validation
- pydantic-settings (environment-based configuration)
- email-validator library

**Utilities:**
- python-json-logger (structured logging)
- aiohttp (HTTP client for async requests)
- python-multipart (form data parsing)

**Development Tools:**
- uv (modern fast Python package manager)
- pytest + pytest-asyncio + pytest-cov (testing)
- ruff (fast linting and formatting, line-length: 100)
- mypy (static type checking in strict mode)
- testcontainers (Docker-based integration tests)

### Frontend Stack

**Core Framework:**
- Angular 20 (latest) with standalone components
- TypeScript 5.8+
- RxJS 7.8+ (reactive programming)

**UI Components & Styling:**
- PrimeNG 19 (Material Design component library)
- TailwindCSS 4.1+ (utility-first CSS)
- Chart.js 4.4+ (analytics visualizations)

**Development & Testing:**
- Playwright 1.56+ (E2E testing)
- Karma + Jasmine (unit testing)
- ESLint + Prettier (code quality)

### Infrastructure Stack

**Containerization:**
- Docker with multi-stage builds
- Docker Compose for orchestration
- Health checks for all services

**Reverse Proxy:**
- Nginx 1.27+ with HTTP/2
- Let's Encrypt SSL certificates
- Rate limiting and security headers

**Database & Caching:**
- PostgreSQL 18-alpine (optimized production)
- Redis 7-alpine (session store and caching)

**CI/CD:**
- GitHub Actions workflows
- GitHub Container Registry (ghcr.io)
- Automated testing, building, and deployment
- Security scanning with Trivy

**Deployment Target:**
- Self-hosted server (Unraid/Linux)
- SSH-based deployment automation
- Rolling updates with health checks

---

## 📁 PROJECT STRUCTURE

```
project-root/
├── back/                              # Backend services (Python)
│   ├── api/                          # Main API service (port 8000)
│   │   ├── views/                    # FastAPI routers (HTTP layer)
│   │   │   ├── auth_view.py
│   │   │   ├── domains_view.py
│   │   │   ├── aliases_view.py
│   │   │   ├── messages_view.py
│   │   │   ├── billing_view.py
│   │   │   ├── subscriptions_view.py
│   │   │   ├── statistics_view.py
│   │   │   ├── users_view.py
│   │   │   ├── admin_view.py
│   │   │   └── webhooks_view.py
│   │   │
│   │   ├── controllers/              # Business logic (pure functions)
│   │   │   ├── aliases_controller.py
│   │   │   ├── billing_controller.py
│   │   │   ├── domains_controller.py
│   │   │   └── messages_controller.py
│   │   │
│   │   ├── database/                 # Database operations (async)
│   │   │   ├── aliases_database.py
│   │   │   ├── billing_database.py
│   │   │   ├── domains_database.py
│   │   │   ├── messages_database.py
│   │   │   └── users_database.py
│   │   │
│   │   ├── schemas/                  # Pydantic models
│   │   │   ├── alias.py
│   │   │   ├── billing.py
│   │   │   ├── domain.py
│   │   │   ├── message.py
│   │   │   └── common.py
│   │   │
│   │   ├── services/                 # External integrations
│   │   │   ├── stripe_service.py
│   │   │   ├── email_service.py
│   │   │   ├── dns_service.py
│   │   │   ├── dkim_service.py
│   │   │   └── dns_adapters.py
│   │   │
│   │   ├── main.py                   # FastAPI app factory
│   │   ├── Dockerfile                # Development build
│   │   └── Dockerfile.prod           # Production multi-stage build
│   │
│   ├── smtp/                         # SMTP server service (port 1025)
│   │   ├── smtp_server/
│   │   │   └── handler.py            # aiosmtpd handler
│   │   ├── forwarding/
│   │   │   └── forwarder.py          # Email forwarding logic
│   │   ├── relay/
│   │   │   ├── direct_smtp.py        # Direct delivery
│   │   │   ├── relay_service.py      # External relay
│   │   │   ├── hybrid_relay.py       # Hybrid strategy
│   │   │   └── dkim_signer.py        # DKIM signing
│   │   ├── config_dns/
│   │   │   └── aliases.yaml          # DNS configuration
│   │   ├── main.py                   # SMTP server entry
│   │   ├── Dockerfile
│   │   └── Dockerfile.prod
│   │
│   ├── shared/                       # Shared modules
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic settings
│   │   │   ├── db.py                 # Database engine
│   │   │   ├── logging_config.py     # JSON logging
│   │   │   └── middlewares.py        # Security & rate limiting
│   │   └── models/                   # SQLAlchemy models
│   │       ├── base.py
│   │       ├── user.py
│   │       ├── domain.py
│   │       ├── alias.py
│   │       ├── message.py
│   │       ├── activity_log.py
│   │       ├── event.py
│   │       └── organization.py
│   │
│   ├── tests/                        # Test suite
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── test_auth_integration.py
│   │   ├── test_auth_unit.py
│   │   ├── test_endpoints.py
│   │   ├── test_messages.py
│   │   ├── test_billing_controller.py
│   │   ├── test_security.py
│   │   └── test_functional_users.py
│   │
│   ├── migrations/                   # Alembic migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │
│   ├── scripts/
│   │   └── seed_dev_db.py            # Development seeding
│   │
│   └── alembic.ini                   # Migration config
│
├── front/                            # Frontend (Angular)
│   ├── src/
│   │   └── app/
│   │       ├── core/                 # Core services
│   │       │   ├── guards/
│   │       │   ├── interceptors/
│   │       │   └── services/
│   │       ├── features/             # Feature modules
│   │       │   ├── domains/
│   │       │   ├── messages/
│   │       │   ├── billing/
│   │       │   ├── dashboard/
│   │       │   └── profile/
│   │       └── shared/               # Shared components
│   │           ├── components/
│   │           └── services/
│   │
│   ├── e2e/                          # Playwright E2E tests
│   ├── angular.json
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── playwright.config.ts
│   ├── nginx.conf                    # Nginx configuration
│   ├── nginx-default.conf
│   └── Dockerfile.prod               # Multi-stage nginx build
│
├── nginx/                            # Reverse proxy configs
│   ├── README.md
│   ├── smtpy.conf
│   └── ssl-setup.sh
│
├── scripts/
│   └── verify-deployment.sh          # Health check script
│
├── docs/                             # Documentation
│
├── .github/
│   ├── workflows/
│   │   └── ci-cd.yml                 # Main CI/CD pipeline
│   └── dependabot.yml                # Dependency updates
│
├── docker-compose.yml                # Basic production
├── docker-compose.dev.yml            # Development setup
├── docker-compose.prod.yml           # Production with scaling
├── pyproject.toml                    # Python project config
├── Makefile                          # Build automation
├── .env.production.template          # Environment template
├── .gitignore
└── README.md
```

---

## 🏗️ ARCHITECTURAL PATTERNS

### 1. Three-Layer Architecture (Backend)

**Layer 1: Views (`*_view.py`)**
- FastAPI router definitions
- HTTP request/response handling
- Request validation with Pydantic schemas
- Dependency injection for sessions
- Status code management
- No business logic

**Layer 2: Controllers (`*_controller.py`)**
- Pure Python functions (no FastAPI dependencies)
- Business logic implementation
- Orchestration of database operations
- Service integration calls
- Error handling and validation
- Framework-agnostic (easily testable)

**Layer 3: Database (`*_database.py`)**
- SQLAlchemy async operations
- Pure data access functions
- Query optimization
- Transaction management
- No business logic

**Benefits:**
- Clean separation of concerns
- Easy unit testing without mocking FastAPI
- Framework-agnostic business logic
- Maintainable and scalable codebase

### 2. Async-First Design

**Backend:**
- All I/O operations use async/await
- FastAPI with async route handlers
- SQLAlchemy with async engine
- aiosmtpd for concurrent email processing
- aiohttp for external API calls

**Frontend:**
- RxJS observables for reactive state
- HTTP interceptors for async operations
- Route guards with async checks

### 3. Authentication & Authorization

**Strategy:**
- Session-based authentication (no JWT)
- HTTP-only cookies for security
- Bcrypt password hashing (cost factor 12)
- CSRF protection via session middleware
- Role-based access control (RBAC)
- Secure session storage in Redis

### 4. Email Delivery Architecture

**Three Delivery Modes:**

1. **Direct Mode:**
   - Self-hosted SMTP directly to recipient servers
   - Full control and zero external costs
   - Requires proper DNS configuration (SPF, DKIM, DMARC, PTR)

2. **Relay Mode:**
   - External SMTP services (Gmail, SendGrid, Mailgun, AWS SES)
   - Higher deliverability rates
   - Per-email costs

3. **Hybrid Mode:**
   - Try direct delivery first
   - Fallback to relay on failure
   - Best of both worlds

### 5. Database Strategy

- PostgreSQL for production (ACID compliance, scalability)
- SQLite for development (fast setup, no external dependencies)
- Alembic for schema migrations (version control)
- Connection pooling with psycopg3
- In-memory SQLite for testing (fast, isolated)

### 6. Frontend Architecture

- Standalone components (no NgModules)
- Service-based state management (no NgRx)
- HTTP interceptors for:
  - Authentication token injection
  - Error handling
  - Loading state management
- Route guards for access control
- Lazy loading for performance

---

## 🐳 DOCKER & CONTAINERIZATION

### Development Setup (`docker-compose.dev.yml`)

```yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./back/api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./back:/app/back          # Hot reload
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app_db
      DEBUG: "true"
      SECRET_KEY: dev-secret-key-change-in-production
      CORS_ORIGINS: http://localhost:4200
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      db:
        condition: service_healthy

  smtp:
    build:
      context: ./back/smtp
      dockerfile: Dockerfile
    ports:
      - "1025:1025"
    volumes:
      - ./back:/app/back
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app_db
    depends_on:
      db:
        condition: service_healthy

  frontend:
    image: node:20
    working_dir: /app
    volumes:
      - ./front:/app
    ports:
      - "4200:4200"
    command: bash -c "npm install && npm start"

volumes:
  postgres_data_dev:

networks:
  default:
    name: app-network
```

### Production Setup (`docker-compose.prod.yml`)

```yaml
services:
  db:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
    networks:
      - app-network

  api:
    image: ${DOCKER_REGISTRY}/${GHCR_OWNER}/app-api:${TAG}
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      IS_PRODUCTION: "true"
      DEBUG: "false"
      CORS_ORIGINS: ${CORS_ORIGINS}
      STRIPE_API_KEY: ${STRIPE_API_KEY}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  smtp:
    image: ${DOCKER_REGISTRY}/${GHCR_OWNER}/app-smtp:${TAG}
    ports:
      - "1025:1025"
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      SMTP_DELIVERY_MODE: ${SMTP_DELIVERY_MODE:-hybrid}
      SMTP_ENABLE_DKIM: ${SMTP_ENABLE_DKIM:-true}
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network

  frontend:
    image: ${DOCKER_REGISTRY}/${GHCR_OWNER}/app-frontend:${TAG}
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro
    restart: unless-stopped
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### Multi-Stage Dockerfile (API Production)

```dockerfile
# Stage 1: Builder
FROM python:3.14-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies into virtual environment
RUN uv sync --all-extras

# Stage 2: Runtime
FROM python:3.14-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY back/ /app/back/

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Set environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production server with 4 workers
CMD ["uvicorn", "back.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Multi-Stage Dockerfile (Frontend Production)

```dockerfile
# Stage 1: Build Angular app
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build --configuration production

# Stage 2: Serve with nginx
FROM nginx:1.27-alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-default.conf /etc/nginx/conf.d/default.conf

# Copy built Angular app
COPY --from=builder /app/dist/app-name/browser /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
```

---

## ⚙️ CI/CD PIPELINE

### GitHub Actions Workflow (`.github/workflows/ci-cd.yml`)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  OWNER: ${{ github.repository_owner }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --all-extras

      - name: Run tests
        run: |
          uv run pytest back/tests/ --cov=back --cov-report=xml --cov-report=html

      - name: Upload coverage reports
        uses: actions/upload-artifact@v4
        with:
          name: coverage-reports
          path: |
            coverage.xml
            htmlcov/

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: pip install uv && uv sync

      - name: Run linter
        run: uv run ruff check back/
        continue-on-error: true

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Run Trivy security scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v4
        with:
          sarif_file: 'trivy-results.sarif'

  build-and-push:
    needs: [test, lint]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    strategy:
      matrix:
        service: [api, smtp, frontend]

    steps:
      - uses: actions/checkout@v5

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.OWNER }}/app-${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ${{ matrix.service == 'frontend' && './front' || './back' }}
          file: ${{ matrix.service == 'frontend' && './front/Dockerfile.prod' || format('./back/{0}/Dockerfile.prod', matrix.service) }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

  deploy:
    needs: [build-and-push]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v5

      - name: Copy deployment files
        uses: appleboy/scp-action@v1.2.2
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          port: ${{ secrets.SSH_PORT }}
          source: "docker-compose.prod.yml,scripts/"
          target: "/srv/app/"

      - name: Deploy to production
        uses: appleboy/ssh-action@v1.2.2
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          port: ${{ secrets.SSH_PORT }}
          script: |
            cd /srv/app

            # Set environment variables
            export DOCKER_REGISTRY=${{ env.REGISTRY }}
            export GHCR_OWNER=${{ env.OWNER }}
            export TAG=latest

            # Load production environment
            echo "${{ secrets.ENV_PRODUCTION_B64 }}" | base64 -d > .env.production

            # Login to registry
            echo "${{ secrets.GITHUB_TOKEN }}" | docker login ${{ env.REGISTRY }} -u ${{ github.actor }} --password-stdin

            # Pull latest images
            docker compose -f docker-compose.prod.yml pull

            # Rolling update
            docker compose -f docker-compose.prod.yml up -d db redis
            sleep 10
            docker compose -f docker-compose.prod.yml up -d smtp
            docker compose -f docker-compose.prod.yml up -d --scale api=2 api
            sleep 5
            docker compose -f docker-compose.prod.yml up -d frontend

            # Cleanup
            docker image prune -f

  health-check:
    needs: [deploy]
    runs-on: ubuntu-latest

    steps:
      - name: Check API health
        run: |
          curl -f https://your-domain.com/health || exit 1

      - name: Check frontend
        run: |
          curl -f https://your-domain.com/ || exit 1
```

---

## 🔐 ENVIRONMENT CONFIGURATION

### `.env.production.template`

```bash
# Database Configuration
POSTGRES_DB=app_production
POSTGRES_USER=postgres
POSTGRES_PASSWORD=  # Generate: openssl rand -base64 32

# Redis Configuration
REDIS_PASSWORD=  # Generate: openssl rand -base64 32

# Application Security
SECRET_KEY=  # Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
DEBUG=false
IS_PRODUCTION=true
LOG_LEVEL=INFO

# Payment Integration (Stripe)
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=https://your-domain.com/billing/success
STRIPE_CANCEL_URL=https://your-domain.com/billing/cancel

# CORS & Networking
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
HTTP_PORT=80
HTTPS_PORT=443
API_PORT=8000
SMTP_PORT=1025

# SMTP Configuration
SMTP_HOSTNAME=mail.your-domain.com
SMTP_DELIVERY_MODE=hybrid  # direct, relay, hybrid
SMTP_ENABLE_DKIM=true

# External SMTP Relay (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=
SMTP_PASSWORD=

# Worker Configuration
API_WORKERS=4  # Recommended: (2 × CPU cores) + 1

# Docker Registry
DOCKER_REGISTRY=ghcr.io
GHCR_OWNER=your-github-username
TAG=latest
```

---

## 📝 CONFIGURATION FILES

### `pyproject.toml`

```toml
[project]
name = "app-backend"
version = "1.0.0"
description = "Production-ready SaaS backend"
requires-python = ">=3.14"

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "psycopg[binary,pool]>=3.1.0",
    "aiosqlite>=0.19.0",
    "alembic>=1.12.0",
    "pydantic>=2.4.0",
    "pydantic-settings>=2.0.0",
    "pydantic[email]>=2.4.0",
    "email-validator>=2.0.0",
    "passlib[bcrypt]>=1.7.4",
    "itsdangerous>=2.1.2",
    "cryptography>=41.0.0",
    "python-json-logger>=2.0.7",
    "stripe>=7.0.0",
    "aiohttp>=3.9.0",
    "python-multipart>=0.0.6",
    "dnspython>=2.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.0",
    "ruff>=0.1.0",
    "mypy>=1.6.0",
    "testcontainers>=3.7.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.mypy]
strict = true
python_version = "3.14"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["back/tests"]
python_files = ["test_*.py", "*_test.py"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["back"]
omit = ["*/tests/*", "*/.venv/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### `Makefile`

```makefile
.PHONY: help install build run stop logs test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies with uv"
	@echo "  make build     - Build Docker containers"
	@echo "  make run       - Start development environment"
	@echo "  make stop      - Stop all containers"
	@echo "  make logs      - View container logs"
	@echo "  make test      - Run test suite"
	@echo "  make lint      - Run code linter"
	@echo "  make format    - Format code"
	@echo "  make clean     - Clean up containers and images"

install:
	pip install uv
	uv sync --all-extras

build:
	docker compose -f docker-compose.dev.yml build

run:
	docker compose -f docker-compose.dev.yml up -d --build

stop:
	docker compose -f docker-compose.dev.yml down

logs:
	docker compose -f docker-compose.dev.yml logs -f

test:
	uv run pytest $(PYTEST_EXTRA_ARGS)

lint:
	uv run ruff check back/

format:
	uv run ruff check --fix back/
	uv run ruff format back/

clean:
	make stop
	docker system prune -f
```

---

## 🚀 IMPLEMENTATION STEPS

### Phase 1: Project Setup (Day 1)

1. **Initialize project structure:**
   ```bash
   mkdir -p back/{api,smtp,shared,tests,migrations,scripts}
   mkdir -p back/api/{views,controllers,database,schemas,services}
   mkdir -p back/smtp/{smtp_server,forwarding,relay}
   mkdir -p back/shared/{core,models}
   mkdir -p front/{src,e2e}
   mkdir -p nginx scripts docs .github/workflows
   ```

2. **Create `pyproject.toml` with all dependencies**

3. **Initialize uv and install dependencies:**
   ```bash
   pip install uv
   uv sync --all-extras
   ```

4. **Set up Git repository:**
   ```bash
   git init
   cp .env.production.template .env.development
   git add .
   git commit -m "Initial project structure"
   ```

### Phase 2: Backend Core (Days 2-5)

1. **Database models** (`back/shared/models/`)
   - Create base model with common fields
   - User model with authentication
   - Domain, alias, message models
   - Organization and activity logging

2. **Core configuration** (`back/shared/core/`)
   - Pydantic settings class
   - Database engine setup
   - JSON logging configuration
   - Security middlewares

3. **Database setup:**
   ```bash
   alembic init back/migrations
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

4. **FastAPI application** (`back/api/main.py`)
   - App factory with lifespan
   - CORS configuration
   - Session middleware
   - Health check endpoint

5. **Authentication system:**
   - Auth views, controllers, database layers
   - Session management
   - Password hashing
   - CSRF protection

### Phase 3: Feature Implementation (Days 6-12)

1. **Domain management:**
   - Views, controllers, database layers
   - DNS verification service
   - CRUD operations

2. **Email aliasing:**
   - Alias CRUD operations
   - Forwarding rules
   - Validation logic

3. **SMTP server** (`back/smtp/`)
   - aiosmtpd handler
   - Email forwarding logic
   - DKIM signing
   - Relay strategies (direct, relay, hybrid)

4. **Message tracking:**
   - Incoming/outgoing message logging
   - Search and filtering
   - Statistics

5. **Billing integration:**
   - Stripe service
   - Subscription management
   - Webhook handling
   - Payment processing

### Phase 4: Frontend Development (Days 13-18)

1. **Angular project setup:**
   ```bash
   cd front
   npm init @angular@latest
   npm install primeng primeicons chart.js
   npx tailwindcss init
   ```

2. **Core services:**
   - HTTP interceptors
   - Auth service and guards
   - API client services

3. **Feature modules:**
   - Dashboard with analytics
   - Domain management UI
   - Alias management UI
   - Message inbox
   - Billing and subscriptions
   - User profile

4. **Shared components:**
   - Layout components
   - Navigation
   - Reusable UI components with PrimeNG

### Phase 5: Testing (Days 19-21)

1. **Backend tests:**
   - Unit tests for controllers
   - Integration tests for views
   - Database operation tests
   - Security tests

2. **Frontend tests:**
   - Component unit tests
   - E2E tests with Playwright

3. **Test fixtures:**
   - Database fixtures with testcontainers
   - Mock services
   - Test data factories

### Phase 6: Docker & Infrastructure (Days 22-24)

1. **Dockerfiles:**
   - Development Dockerfiles for API and SMTP
   - Multi-stage production Dockerfiles
   - Frontend nginx Dockerfile

2. **Docker Compose:**
   - Development compose file
   - Production compose file
   - Health checks and dependencies

3. **Nginx configuration:**
   - Reverse proxy setup
   - SSL/TLS configuration
   - Rate limiting
   - Security headers

### Phase 7: CI/CD (Days 25-26)

1. **GitHub Actions workflow:**
   - Test job with coverage
   - Lint and security scanning
   - Docker build and push
   - Deployment automation

2. **Deployment scripts:**
   - SSH deployment script
   - Health check verification
   - Rollback procedures

### Phase 8: Production Readiness (Days 27-30)

1. **Security hardening:**
   - Environment variable validation
   - Rate limiting configuration
   - CORS configuration
   - Security headers

2. **Monitoring & logging:**
   - Structured JSON logging
   - Health check endpoints
   - Error tracking setup

3. **Documentation:**
   - README with setup instructions
   - API documentation with FastAPI
   - Deployment guide
   - Environment variable documentation

4. **DNS configuration:**
   - SPF, DKIM, DMARC records
   - Reverse DNS (PTR)
   - SSL certificates

5. **Production deployment:**
   - Server setup
   - Docker Compose deployment
   - SSL certificate installation
   - Initial data seeding

---

## ✅ PRODUCTION CHECKLIST

### Security
- [ ] All environment variables stored securely (GitHub Secrets)
- [ ] Passwords hashed with bcrypt (cost factor ≥12)
- [ ] Session cookies HTTP-only and Secure
- [ ] CSRF protection enabled
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] SQL injection protection (parameterized queries)
- [ ] Input validation with Pydantic
- [ ] Secrets rotation process

### Infrastructure
- [ ] Multi-stage Docker builds
- [ ] Health checks on all services
- [ ] Resource limits configured
- [ ] Logging with rotation
- [ ] Database backups automated
- [ ] Redis persistence enabled
- [ ] Non-root user in containers
- [ ] Docker image scanning (Trivy)

### Deployment
- [ ] CI/CD pipeline tested
- [ ] Deployment rollback procedure
- [ ] Environment-specific configs
- [ ] Database migration strategy
- [ ] Zero-downtime deployment
- [ ] Post-deployment health checks

### Email Deliverability
- [ ] SPF record configured
- [ ] DKIM signing enabled
- [ ] DMARC policy set
- [ ] Reverse DNS (PTR) configured
- [ ] Firewall port 25 open
- [ ] Email authentication tested
- [ ] Bounce handling implemented

### Monitoring
- [ ] Health endpoints working
- [ ] Structured logging enabled
- [ ] Error tracking configured
- [ ] Performance monitoring
- [ ] Database query optimization
- [ ] API response time tracking

### Testing
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests
- [ ] E2E tests with Playwright
- [ ] Load testing completed
- [ ] Security testing done
- [ ] Accessibility testing

### Documentation
- [ ] README complete
- [ ] API documentation
- [ ] Deployment guide
- [ ] Architecture documentation
- [ ] Troubleshooting guide
- [ ] Contribution guidelines

---

## 🎓 KEY LEARNINGS & BEST PRACTICES

### Backend Best Practices

1. **3-Layer Architecture:**
   - Keep views thin (HTTP only)
   - Business logic in controllers
   - Database operations isolated
   - Easy to test and maintain

2. **Async Everything:**
   - Use async/await for all I/O
   - Connection pooling for database
   - Concurrent email processing
   - Better resource utilization

3. **Configuration Management:**
   - Pydantic settings for type safety
   - Environment-based configuration
   - Validation at startup
   - Clear error messages

4. **Database Migrations:**
   - Always use Alembic
   - Version control migrations
   - Test migrations in development
   - Backup before production migrations

### Frontend Best Practices

1. **Standalone Components:**
   - Modern Angular approach
   - Better tree-shaking
   - Lazy loading friendly
   - Simpler testing

2. **Service-Based State:**
   - RxJS for reactive state
   - HTTP interceptors for cross-cutting
   - No need for complex state management
   - Easier to understand

3. **UI Component Library:**
   - PrimeNG for consistency
   - TailwindCSS for customization
   - Faster development
   - Professional appearance

### DevOps Best Practices

1. **Multi-Stage Builds:**
   - Smaller production images
   - Security through minimalism
   - Faster deployments
   - Layer caching

2. **Health Checks:**
   - All services must have health checks
   - Start period for slow services
   - Proper retry configuration
   - Database connectivity checks

3. **Rolling Updates:**
   - Database first
   - API with multiple replicas
   - Frontend last
   - Zero downtime

4. **Environment Isolation:**
   - Separate dev/prod configs
   - Secrets in GitHub Secrets
   - Base64 encoding for multi-line
   - Never commit secrets

### Email Deliverability

1. **DNS Configuration is Critical:**
   - SPF prevents spoofing
   - DKIM proves authenticity
   - DMARC sets policy
   - PTR for reputation

2. **Delivery Strategy:**
   - Hybrid mode recommended
   - Monitor bounce rates
   - Implement retry logic
   - Track delivery metrics

3. **SMTP Relay vs Direct:**
   - Relay: Better deliverability, cost per email
   - Direct: Full control, requires DNS setup
   - Hybrid: Best of both worlds

---

## 🔧 TROUBLESHOOTING GUIDE

### Common Issues

**Issue: Database connection fails**
```bash
# Check if database is healthy
docker compose ps db
docker compose logs db

# Verify connection string
echo $DATABASE_URL

# Test connection
docker compose exec api python -c "from back.shared.core.db import engine; print(engine)"
```

**Issue: Frontend can't reach API**
```bash
# Check CORS configuration
grep CORS_ORIGINS .env.production

# Verify nginx proxy
docker compose logs frontend

# Test API endpoint
curl http://localhost:8000/health
```

**Issue: Emails not being delivered**
```bash
# Check SMTP server
docker compose logs smtp

# Verify DNS records
dig TXT _dmarc.your-domain.com
dig TXT default._domainkey.your-domain.com

# Test DKIM signing
python back/test_dns_verification.py
```

**Issue: CI/CD deployment fails**
```bash
# Check GitHub Actions logs
# Verify secrets are set
# Test SSH connection
ssh -p 2345 user@server "docker ps"

# Verify images were pushed
docker pull ghcr.io/owner/app-api:latest
```

---

## 📚 ADDITIONAL RESOURCES

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Angular Documentation:** https://angular.dev/
- **PostgreSQL Best Practices:** https://wiki.postgresql.org/wiki/Don%27t_Do_This
- **Docker Multi-Stage Builds:** https://docs.docker.com/build/building/multi-stage/
- **GitHub Actions:** https://docs.github.com/en/actions
- **Email Deliverability:** https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/
- **Nginx Configuration:** https://nginx.org/en/docs/
- **Stripe Integration:** https://stripe.com/docs/api

---

## 🎯 FINAL NOTES

This architecture is production-tested and handles:
- **High concurrency** with async Python
- **Scalability** with horizontal API scaling
- **Security** with industry best practices
- **Observability** with structured logging
- **Maintainability** with clean architecture
- **Cost efficiency** with optimized containers

**Estimated Development Time:** 30 days for a solo developer, 15 days for a 2-person team.

**Infrastructure Costs (Monthly):**
- VPS/Server: $20-50
- PostgreSQL managed: $15-30 (or self-hosted: $0)
- Redis managed: $10-20 (or self-hosted: $0)
- Stripe fees: Per transaction
- Domain + SSL: $15/year

**Total self-hosted:** ~$20-50/month

---

Good luck building your SaaS platform! 🚀
