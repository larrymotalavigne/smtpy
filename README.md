# SMTPy v2

A self-hosted email forwarding and domain management service built with FastAPI, SQLAlchemy (async), and Stripe integration.

## Features

- **Domain Management**: CRUD operations for email domains with DNS verification
- **Message Processing**: Track and manage forwarded email messages
- **Billing Integration**: Stripe-powered subscription management
- **Async Architecture**: Built with async/await for high performance
- **PostgreSQL Database**: Reliable data storage with Alembic migrations
- **Function-Based Architecture**: Clean 3-layer architecture (view → controller → database)

## Architecture

SMTPy v2 follows a strict 3-layer module structure:

- **Views** (`*_view.py`): FastAPI routers with request/response handling
- **Controllers** (`*_controller.py`): Business logic orchestration (no FastAPI imports)
- **Database** (`*_database.py`): Pure SQLAlchemy async queries

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13+ (for local development)
- PostgreSQL 16+ (handled by Docker)

### Setup

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

3. **Start the services:**
   ```bash
   make build
   make run
   ```

4. **Check the logs:**
   ```bash
   make logs
   ```

The API will be available at `http://localhost:8000`

### Environment Variables

Configure these variables in your `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/smtpy

# Stripe Configuration
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=http://localhost:8000/billing/success
STRIPE_CANCEL_URL=http://localhost:8000/billing/cancel
STRIPE_PORTAL_RETURN_URL=http://localhost:8000/billing

# API Settings
DEBUG=true
SECRET_KEY=change-this-secret-key-in-production
```

## API Documentation

### Health Check

```bash
# Basic health check
curl http://localhost:8000/

# Detailed health check with features
curl http://localhost:8000/health
```

### Domain Management

#### Create a Domain
```bash
curl -X POST "http://localhost:8000/domains" \
  -H "Content-Type: application/json" \
  -d '{"name": "example.com"}'
```

#### List Domains
```bash
# Basic listing
curl "http://localhost:8000/domains"

# With pagination
curl "http://localhost:8000/domains?page=1&page_size=10"
```

#### Get Domain Details
```bash
curl "http://localhost:8000/domains/1"
```

#### Verify Domain DNS
```bash
curl -X POST "http://localhost:8000/domains/1/verify"
```

#### Get Required DNS Records
```bash
curl "http://localhost:8000/domains/1/dns-records"
```

#### Update Domain Settings
```bash
curl -X PATCH "http://localhost:8000/domains/1" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

#### Delete Domain
```bash
curl -X DELETE "http://localhost:8000/domains/1"
```

### Message Management

#### List Messages
```bash
# Basic listing
curl "http://localhost:8000/messages"

# With filters
curl "http://localhost:8000/messages?status=delivered&domain_id=1&page=1&page_size=20"

# Filter by date range
curl "http://localhost:8000/messages?date_from=2025-01-01&date_to=2025-12-31"

# Filter by sender/recipient
curl "http://localhost:8000/messages?sender_email=user@example.com"
```

#### Search Messages
```bash
curl "http://localhost:8000/messages/search?q=important"
```

#### Get Message Statistics
```bash
# Overall stats
curl "http://localhost:8000/messages/stats"

# Stats since specific date
curl "http://localhost:8000/messages/stats?since=2025-01-01"
```

#### Get Recent Messages
```bash
curl "http://localhost:8000/messages/recent?limit=5"
```

#### Get Message Details
```bash
curl "http://localhost:8000/messages/123"
```

#### Get Messages by Domain
```bash
curl "http://localhost:8000/messages/domain/1?page=1&page_size=20"
```

#### Get Messages by Thread
```bash
curl "http://localhost:8000/messages/thread/thread-id-123"
```

#### Update Message Status
```bash
curl -X PATCH "http://localhost:8000/messages/123/status?new_status=delivered&forwarded_to=user@example.com"
```

#### Delete Message
```bash
curl -X DELETE "http://localhost:8000/messages/123"
```

### Billing Management

#### Create Checkout Session
```bash
curl -X POST "http://localhost:8000/billing/checkout-session" \
  -H "Content-Type: application/json" \
  -d '{"price_id": "price_1234567890"}'
```

#### Get Customer Portal
```bash
curl "http://localhost:8000/billing/customer-portal"
```

#### Get Current Subscription
```bash
curl "http://localhost:8000/subscriptions/me"
```

#### Cancel Subscription
```bash
curl -X PATCH "http://localhost:8000/subscriptions/cancel" \
  -H "Content-Type: application/json" \
  -d '{"cancel_at_period_end": true}'
```

#### Resume Subscription
```bash
curl -X PATCH "http://localhost:8000/subscriptions/resume"
```

#### Get Organization Billing Info
```bash
curl "http://localhost:8000/billing/organization"
```

#### Stripe Webhook (for Stripe to call)
```bash
curl -X POST "http://localhost:8000/webhooks/stripe" \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: t=..." \
  -d '{...stripe event data...}'
```

## Development

### Local Development Setup

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Run tests:**
   ```bash
   make test
   ```

3. **Run the API locally:**
   ```bash
   cd back
   uvicorn api.main:create_app --reload --host 0.0.0.0 --port 8000 --factory
   ```

### Database Migrations

```bash
# Create a new migration
cd back
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

The project includes comprehensive tests covering:

- API endpoints (FastAPI TestClient)
- Controller business logic
- Database operations
- Schema validation

```bash
# Run all tests
make test

# Run specific test file
pytest back/tests/test_messages.py -v

# Run with coverage
pytest --cov=back/api back/tests/
```

## API Response Formats

### Paginated Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### Error Response
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "code": "ERROR_CODE"
}
```

### Domain Response
```json
{
  "id": 1,
  "name": "example.com",
  "organization_id": 1,
  "status": "verified",
  "is_active": true,
  "mx_record_verified": true,
  "spf_record_verified": true,
  "dkim_record_verified": true,
  "dmarc_record_verified": true,
  "dkim_public_key": "...",
  "verification_token": "...",
  "created_at": "2025-09-01T18:10:00Z",
  "updated_at": "2025-09-01T18:10:00Z"
}
```

### Message Response
```json
{
  "id": 123,
  "message_id": "unique-message-id",
  "thread_id": "thread-id-123",
  "domain_id": 1,
  "sender_email": "sender@example.com",
  "recipient_email": "recipient@example.com",
  "forwarded_to": "user@example.com",
  "subject": "Email Subject",
  "body_preview": "Email body preview...",
  "status": "delivered",
  "error_message": null,
  "size_bytes": 1024,
  "has_attachments": false,
  "created_at": "2025-09-01T18:10:00Z",
  "updated_at": "2025-09-01T18:10:00Z"
}
```

### Message Statistics
```json
{
  "total_messages": 1000,
  "delivered_messages": 950,
  "failed_messages": 30,
  "pending_messages": 20,
  "total_size_bytes": 1048576
}
```

## Message Status Values

- `pending`: Message received, awaiting processing
- `processing`: Message is being processed
- `delivered`: Message successfully forwarded
- `failed`: Message processing failed
- `bounced`: Message bounced back
- `rejected`: Message rejected by filters

## Domain Status Values

- `pending`: Domain added, awaiting verification
- `verified`: All DNS records verified
- `failed`: Domain verification failed

## Docker Commands

```bash
# Build images
make build

# Start services
make run

# Stop services
make stop

# View logs
make logs

# Clean up
make clean
```

## Production Deployment

1. **Set production environment variables:**
   - Set `DEBUG=false`
   - Use strong `SECRET_KEY`
   - Configure production database URL
   - Set up real Stripe keys

2. **Database setup:**
   - Ensure PostgreSQL is running
   - Run migrations: `alembic upgrade head`

3. **Reverse proxy setup:**
   - Configure nginx or similar for SSL termination
   - Set up proper domain and SSL certificates

4. **Monitoring:**
   - Set up logging aggregation
   - Configure health checks
   - Monitor database performance

## Architecture Notes

### File Naming Conventions

Follow these naming conventions for consistency across the codebase:

- **View files**: Files under `routers/` directories should end with `_view.py` (e.g., `domains_view.py`, `messages_view.py`)
- **Controller files**: Files under `controllers/` directories should end with `_controller.py` (e.g., `domains_controller.py`, `messages_controller.py`) 
- **Database files**: Files under `repositories/` directories should end with `_database.py` (e.g., `domains_database.py`, `messages_database.py`)

This convention helps distinguish between different types of modules and maintains consistency across the project structure.

