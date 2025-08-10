# SMTPy Development Guidelines

## Project Overview
SMTPy is an email aliasing and forwarding service (Addy.io clone) built with FastAPI, SQLAlchemy, and aiosmtpd. It provides a web interface for managing email domains, aliases, and forwarding rules with DKIM/SPF/DMARC support.

## Build/Configuration Instructions

### Package Management
- **Package Manager**: Uses `uv` as the primary package manager and build system
- **Python Version**: Requires Python >=3.9 (Docker uses Python 3.13-slim)
- **Dependencies**: Defined in `pyproject.toml` only (requirements.txt has been removed)

### Development Setup
1. **Local Development**:
   ```bash
   # Install dependencies
   uv sync
   
   # Run the application
   python main.py
   # OR
   uvicorn main:create_app --reload --host 0.0.0.0 --port 8000 --factory
   ```

2. **Docker Development**:
   ```bash
   # Build and run development environment
   make build
   make run
   
   # View logs
   make logs
   
   # Stop containers
   make stop
   ```

### Environment Variables
Configure these environment variables for proper operation:
- `SMTPY_SECRET_KEY`: Session secret key (default: "change-this-secret-key")
- `SMTPY_DB_PATH`: Database file path (default: varies by environment)
- `SMTP_HOST`: SMTP relay host (default: "localhost")
- `SMTP_PORT`: SMTP relay port (default: 25)
- `STRIPE_TEST_API_KEY`: Stripe API key for billing
- `STRIPE_BILLING_PORTAL_RETURN_URL`: Stripe billing portal return URL

### Database Setup
- Uses SQLite by default with SQLAlchemy ORM
- Database initialization happens automatically on app startup via `init_db()`
- Creates default admin user (username: "admin", password: "password") if no users exist
- Alembic is configured for database migrations

## Testing Information

### Test Configuration
- **Framework**: pytest with pytest-asyncio
- **Test Database**: In-memory SQLite with shared cache
- **Test Client**: FastAPI TestClient for HTTP endpoint testing

### Running Tests
```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run specific test
python -m pytest tests/test_basic.py::test_landing_page -v

# Run with coverage
python -m pytest --cov=. tests/
```

### Test Structure
- `tests/conftest.py`: Test database setup and fixtures
- `tests/test_basic.py`: Basic functionality tests
- `tests/test_endpoints.py`: Comprehensive endpoint testing

### Adding New Tests
1. Create test files in the `tests/` directory
2. Use the `TestClient` from FastAPI for HTTP testing
3. Tests automatically use the in-memory test database
4. Email sending functions are automatically mocked in tests

### Test Database Behavior
- Each test session uses a fresh in-memory SQLite database
- Database tables are created automatically before tests
- All tables are dropped after test completion
- Email sending functions are mocked to prevent actual email sending

## Code Architecture

### Application Structure
- **Entry Point**: `main.py` with `create_app()` factory function
- **Views**: Modular routers in `views/` directory
  - `main_view.py`: Authentication, registration, main pages
  - `user_view.py`: User management
  - `domain_view.py`: Domain management
  - `alias_view.py`: Email alias management
  - `billing_view.py`: Stripe billing integration
- **Models**: Database models in `database/models.py`
- **Database**: Database calls in `database/`
- **Controllers**: Business logic in `controllers/`
- **Utils**: Helper functions in `utils/`

### Key Components
- **SMTP Server**: `smtp_server/handler.py` for email processing
- **Email Forwarding**: `forwarding/forwarder.py` for email routing
- **DNS Configuration**: `config_dns/` for DNS record management
- **Templates**: Jinja2 templates in `templates/`

### Configuration Management
- Uses `pydantic-settings` for environment-based configuration
- Configuration class in `config.py` with `SETTINGS` global instance
- Template configuration integrated into settings

## Development Notes

### Code Style Notes
- Uses FastAPI with dependency injection patterns
- SQLAlchemy v2 ORM with session management via context managers
- Password hashing with bcrypt via passlib
- Session-based authentication (not JWT)
- Background tasks for email sending
- **Use function-based logic and not class-based**: Prefer standalone functions over class-based implementations for business logic
- **Do not use alias in import**: Import statements should not use aliases (avoid `import module as alias` patterns)

### Database Patterns
- Uses `get_db()` context manager for database operations
- Models inherit from SQLAlchemy Base
- Relationships defined with `selectinload` for eager loading
- Activity logging implemented for audit trails

### Security Considerations
- CSRF protection via session middleware
- Password hashing with bcrypt
- Email verification for new accounts
- Role-based access control (admin/user roles)
- Invitation-based registration system

### Email Processing
- DKIM signing support via dkimpy
- DNS record validation for SPF/DKIM/DMARC
- Email forwarding with configurable SMTP relay
- Catch-all domain support

### Development Workflow
1. Use `make build` and `make run` for Docker development
2. Run tests before committing changes
3. Check DNS configuration for email domains
4. Monitor logs via `make logs`
5. Use admin panel at `/admin` for domain/alias management

### Debugging Tips
- Default admin credentials: admin/password
- Check database file permissions for SQLite issues
- Verify SMTP relay configuration for email forwarding
- Use DNS check endpoints for troubleshooting domain setup
- Monitor activity logs for email processing issues