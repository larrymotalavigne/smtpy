# SMTPy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Angular 20](https://img.shields.io/badge/angular-20-red.svg)](https://angular.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A self-hosted email aliasing and forwarding service built with FastAPI, SQLAlchemy, and aiosmtpd. SMTPy provides a comprehensive solution for managing email domains, aliases, and forwarding rules with DKIM/SPF/DMARC support and Stripe billing integration.

**Project Status**: 🚀 **DEPLOYED IN PRODUCTION** (98% Complete) - Fully deployed at https://smtpy.fr with Nginx Proxy Manager, Docker Mail Server integration, CI/CD pipeline, and automated deployments. Core features complete with self-hosted SMTP, Stripe billing, comprehensive monitoring, and production infrastructure.

## Features

### Backend (97% Complete)
- **Email Aliasing & Forwarding**: Create and manage email aliases with automatic forwarding
- **Domain Management**: CRUD operations for email domains with DNS verification
- **SMTP Server**: Built-in SMTP server for receiving and processing emails
- **Message Processing**: Track and manage forwarded email messages
- **DNS Configuration**: Automatic DNS record generation and verification (MX, SPF, DKIM, DMARC)
- **Billing Integration**: Stripe-powered subscription management
- **Async Architecture**: Built with async/await for high performance
- **DKIM Signing**: Email signing support for enhanced deliverability
- **Security**: Rate limiting, security headers (CSP, HSTS), CORS configuration
- **Logging**: JSON structured logging for production monitoring
- **Testing**: Comprehensive test suite with 97% pass rate (96/99 tests passing)

### Frontend (100% Complete)
- **Modern UI**: Angular 19 with PrimeNG and TailwindCSS
- **Dashboard**: Real-time metrics with 7-day statistics and activity charts
- **Domain Management**: Full CRUD operations with DNS configuration wizard
- **Message Management**: List, filter, view, retry, and delete messages
- **Statistics & Analytics**: Time-series charts, domain breakdown, top aliases
- **Billing & Subscriptions**: Stripe checkout integration with usage tracking
- **User Profile**: Account management, password changes, API keys
- **Settings**: Notification preferences and app configuration
- **Responsive Design**: Mobile, tablet, and desktop support

## Technology Stack

### Backend
- **Python**: >=3.13
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy v2 with async support
- **SMTP Server**: aiosmtpd for email processing
- **Email Processing**: dkimpy for DKIM signing, dnspython for DNS operations
- **Authentication**: Session-based with bcrypt password hashing
- **Billing**: Stripe integration for subscription management
- **Package Manager**: uv (modern Python package manager)

### Frontend
- **Framework**: Angular 19 with standalone components
- **UI Library**: PrimeNG 19 (Material Design-inspired components)
- **Styling**: TailwindCSS 4 (utility-first CSS framework)
- **Charts**: Chart.js 4 (for statistics and analytics)
- **HTTP Client**: Angular HttpClient with RxJS Observables
- **State Management**: RxJS + Services (no NgRx)
- **Authentication**: Session-based with HTTP-only cookies

### Infrastructure & Deployment
- **Containerization**: Docker with multi-stage production Dockerfiles
- **Orchestration**: Docker Compose with health checks, resource limits, and HA setup
- **CI/CD**: GitHub Actions with automated testing, security scanning, and deployments
- **Registry**: GitHub Container Registry (GHCR) for Docker images
- **Reverse Proxy**: Nginx Proxy Manager (shared infrastructure)
- **Mail Server**: Docker Mail Server (Postfix, Dovecot, Rspamd, DKIM/DMARC)
- **Monitoring**: VictoriaMetrics + Grafana (shared infrastructure)
- **Database Migrations**: Alembic with automated deployment integration
- **Testing**: pytest with pytest-asyncio, Playwright E2E tests
- **Security**: Trivy vulnerability scanning, automated updates via Dependabot

## Requirements

- **Python**: >=3.13
- **Package Manager**: uv
- **Database**: PostgreSQL 16+ (production) or SQLite (development)
- **Docker & Docker Compose**: For containerized deployment

## Quick Start

### Prerequisites

1. Install Python 3.13+
2. Install uv: `pip install uv`
3. Install Docker and Docker Compose

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd smtpy
   ```

2. **Environment Configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies:**
   ```bash
   make install
   ```

4. **Start development environment with Docker:**
   ```bash
   make build
   make run
   ```

   Or start services individually:
   ```bash
   # Start with development compose (includes SMTP server)
   docker compose -f docker-compose.dev.yml up -d
   ```

5. **Check the logs:**
   ```bash
   make logs
   ```

The services will be available at:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:4200 (development) or http://localhost (production)
- **SMTP Server**: localhost:1025 (development)

### Local Development (without Docker)

1. **Run the API server:**
   ```bash
   cd back/api
   uvicorn main:create_app --reload --host 0.0.0.0 --port 8000 --factory
   ```

2. **Run the SMTP server (separate terminal):**
   ```bash
   cd back/smtp
   python main.py
   ```

3. **Run the frontend (separate terminal):**
   ```bash
   cd front
   npm install
   npm start
   # Access at http://localhost:4200
   ```

## Environment Variables

Configure these variables in your `.env` file:

### Database Configuration
```bash
# Production (PostgreSQL)
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/smtpy

# Development (SQLite)
SMTPY_DB_PATH=/path/to/dev.db
```

### API Settings
```bash
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
SECRET_KEY=change-this-secret-key-in-production
```

### Stripe Configuration
```bash
STRIPE_API_KEY=sk_test_your_stripe_api_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_SUCCESS_URL=http://localhost:8000/billing/success
STRIPE_CANCEL_URL=http://localhost:8000/billing/cancel
STRIPE_PORTAL_RETURN_URL=http://localhost:8000/billing
```

### SMTP Configuration
```bash
SMTP_HOST=localhost
SMTP_PORT=1025
```

### DNS Configuration
```bash
DNS_CHECK_ENABLED=true
```

### Docker Environment
```bash
POSTGRES_DB=smtpy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## Available Scripts

The project includes a Makefile with the following commands:

```bash
# Install dependencies
make install

# Build Docker images
make build

# Start the application stack
make run

# Stop the application stack
make stop

# View container logs
make logs

# Run tests
make test

# Clean up Docker resources
make clean

# Show all available commands
make help
```

## Testing

The project uses pytest with comprehensive test coverage:

### Test Structure
- **Location**: `back/tests/`
- **Framework**: pytest with pytest-asyncio
- **Database**: In-memory SQLite for testing
- **Coverage**: API endpoints, controllers, database operations, schema validation

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest back/tests/test_messages.py -v

# Run with coverage
pytest --cov=back/api back/tests/

# Run specific test markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
```

### Test Configuration
- Tests automatically use in-memory SQLite database
- Email sending functions are mocked in tests
- Database tables are created/dropped automatically for each test session

## Database Management

### Migrations

The project uses Alembic for database migrations:

```bash
cd back/api

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show migration history
alembic history
```

### Database Initialization
- Database tables are created automatically on application startup
- Default admin user is created if no users exist (username: "admin", password: "password")

## Project Structure

```
smtpy/
├── back/
│   ├── api/                    # FastAPI application
│   │   ├── core/               # Core configuration and database
│   │   ├── database/           # Database layer (*_database.py)
│   │   ├── controllers/        # Business logic (*_controller.py)
│   │   ├── views/              # API routers (*_view.py)
│   │   ├── models/             # Database models
│   │   ├── services/           # External service integrations
│   │   ├── static/             # Static files
│   │   └── main.py             # API entry point
│   ├── smtp/                   # SMTP server components
│   │   ├── smtp_server/        # SMTP server implementation
│   │   ├── forwarding/         # Email forwarding logic
│   │   ├── config_dns/         # DNS configuration utilities
│   │   └── main.py             # SMTP server entry point
│   └── tests/                  # Test suite
├── front/                      # Angular 19 frontend application
│   ├── src/app/
│   │   ├── core/               # Services, guards, interceptors, interfaces
│   │   ├── features/           # Feature components (domains, messages, billing, etc.)
│   │   ├── shared/             # Shared components (layout, etc.)
│   │   └── app.routes.ts       # Application routing
│   ├── package.json            # NPM dependencies
│   └── angular.json            # Angular configuration
├── docs/                       # Documentation
│   └── tasks.md                # Project tasks and status
├── docker-compose.yml          # Production Docker setup
├── docker-compose.dev.yml      # Development Docker setup
├── pyproject.toml              # Python project configuration
├── Makefile                    # Development commands
└── .env.example                # Environment variables template
```

## Architecture

SMTPy follows a strict 3-layer architecture:

### Layer Structure
- **Views** (`*_view.py`): FastAPI routers with request/response handling and routing logic
- **Controllers** (`*_controller.py`): Pure functions orchestrating business logic (no FastAPI imports)
- **Database** (`*_database.py`): Pure SQLAlchemy async queries accepting AsyncSession as first argument

### Key Principles
- Function-based logic over class-based implementations
- No import aliases (avoid `import module as alias`)
- Controllers accept explicit dependencies (db, services, etc.)
- Views inject dependencies and pass them to controllers
- Database functions are pure async functions

## API Documentation

### Health Check Endpoints

```bash
# Basic health check
curl http://localhost:8000/

# Detailed health check
curl http://localhost:8000/health
```

### Main Features
- **Domain Management**: Create, verify, and manage email domains
- **Message Processing**: Track forwarded emails and message statistics
- **Billing**: Stripe integration for subscription management

For detailed API documentation, visit http://localhost:8000/docs when the application is running.

## Production Deployment

**Current Status**: ✅ **LIVE IN PRODUCTION**
- **URL**: https://smtpy.fr
- **Deployment**: Automated via GitHub Actions on push to `main`
- **Infrastructure**: Shared server with Nginx Proxy Manager, Docker Mail Server, VictoriaMetrics, Grafana
- **Database**: PostgreSQL 18 with automated backups
- **Caching**: Redis 7 for sessions and rate limiting
- **High Availability**: 2 API replicas with zero-downtime deployments

### Provide .env.production via GitHub Secrets

You can store the entire .env.production in GitHub Secrets and let the deploy workflow recreate it securely on the server.

Recommended approach (base64-encoded):

1. Create and verify your .env.production locally (use .env.production.template as a guide).
2. Base64-encode the file (no line wrapping):
   - macOS/Linux (BSD base64):
     - cat .env.production | base64 > env.b64
   - GNU coreutils (Linux):
     - base64 -w0 .env.production > env.b64
3. Copy the contents of env.b64 and create a new GitHub repository secret named ENV_PRODUCTION_B64 with that value.
4. The CI/CD workflow will decode this secret on the server into /srv/smtpy/.env.production and pass it to docker compose via --env-file.

Alternative (plaintext secret):

- Create a secret named ENV_PRODUCTION containing the raw file content. This works, but long multi-line secrets are more reliable and safer when base64-encoded. Note: our workflow prefers ENV_PRODUCTION_B64 when both are set.

Fallback (individual secrets):

- If neither ENV_PRODUCTION_B64 nor ENV_PRODUCTION is present, the deploy step falls back to individual secrets that docker-compose.prod.yml requires. Ensure these repository secrets exist:
  - POSTGRES_PASSWORD
  - REDIS_PASSWORD
  - SECRET_KEY
  - STRIPE_API_KEY
  - STRIPE_WEBHOOK_SECRET

Security notes:

- Do not commit .env.production to the repo. It is already .gitignore'd.
- Use strong, unique values and rotate regularly.
- If your org enforces SSO for GHCR, enable SSO on the PAT used in the workflow (secret PAT).

### Docker Deployment

1. **Configure production environment:**
   ```bash
   cp .env.example .env
   # Edit .env with production values:
   # - Set DEBUG=false
   # - Use strong SECRET_KEY
   # - Configure production DATABASE_URL
   # - Set real Stripe keys
   ```

2. **Start production services:**
   ```bash
   docker compose up -d
   ```

### Database Setup
- Ensure PostgreSQL is running and accessible
- Migrations run automatically on container startup
- For manual migration: `docker exec <api-container> alembic upgrade head`

### Reverse Proxy Setup
- Configure nginx or similar for SSL termination
- Set up proper domain and SSL certificates
- Forward traffic to port 8000 (API) and port 80/443 (frontend)
- Ensure frontend is built with `npm run build` and served from `front/dist/smtpy-frontend/`

### Monitoring
- Set up logging aggregation
- Configure health check monitoring
- Monitor database performance
- Track email processing metrics

## Development Guidelines

### Code Style
- Follow the 3-layer architecture pattern
- Use function-based implementations
- Avoid import aliases
- Password hashing with bcrypt
- Session-based authentication (not JWT)
- Background tasks for email sending

### Security Considerations
- CSRF protection via session middleware
- Password hashing with bcrypt
- Email verification for new accounts
- Role-based access control (admin/user roles)
- Invitation-based registration system

### Email Processing
- DKIM signing support
- DNS record validation for SPF/DKIM/DMARC
- Email forwarding with configurable SMTP relay
- Catch-all domain support

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Check DATABASE_URL or SMTPY_DB_PATH configuration
   - Ensure PostgreSQL is running (production) or SQLite file permissions (development)

2. **Email Processing Issues**:
   - Verify SMTP_HOST and SMTP_PORT configuration
   - Check DNS configuration for domains
   - Monitor activity logs for email processing errors

3. **Docker Issues**:
   - Run `make clean` to remove old containers and images
   - Check container logs with `make logs`
   - Ensure ports 8000, 3000, and 1025 are not in use

### Admin Access
- Default admin credentials: username="admin", password="password"
- Change default credentials in production
- Use admin panel for domain and alias management

## Contributing

### Development Workflow
1. Use `make build` and `make run` for Docker development
2. Run `make test` before committing changes
3. Follow the 3-layer architecture pattern
4. Check DNS configuration for email domains
5. Monitor logs via `make logs`

### Code Quality
- Code formatting with Black (line length: 100)
- Linting with Ruff
- Type checking with MyPy
- Pre-commit hooks available

## License

**TODO**: License information needs to be added. Please add a LICENSE file to specify the project's license terms.

## Support

**TODO**: Add support information, contributing guidelines, and contact details.

## Changelog

**TODO**: Add changelog or link to releases for version history.

