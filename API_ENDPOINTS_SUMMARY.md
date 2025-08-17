# SMTPy Comprehensive REST API Implementation

## Overview

This implementation provides a complete REST API for SMTPy email aliasing service, based on ImprovMX-style API patterns. All endpoints are
available under `/api/v1/` prefix.

## Implemented Endpoints

### Account Management

- `GET /api/v1/account` - Get current account information
- `PATCH /api/v1/account` - Update account information

### Domain Management

- `GET /api/v1/domains` - List all domains for authenticated user
- `POST /api/v1/domains` - Create a new domain
- `GET /api/v1/domains/{domain_id}` - Get domain details
- `PATCH /api/v1/domains/{domain_id}` - Update domain settings
- `DELETE /api/v1/domains/{domain_id}` - Delete a domain
- `GET /api/v1/domains/{domain_id}/dns` - Check DNS configuration for domain
- `POST /api/v1/domains/{domain_id}/dns/check` - Trigger DNS record check for domain

### Alias Management

- `GET /api/v1/domains/{domain_id}/aliases` - List all aliases for a domain
- `POST /api/v1/domains/{domain_id}/aliases` - Create a new alias for domain
- `GET /api/v1/aliases` - List all aliases (optionally filtered by domain)
- `GET /api/v1/aliases/{alias_id}` - Get alias details
- `PATCH /api/v1/aliases/{alias_id}` - Update alias settings
- `DELETE /api/v1/aliases/{alias_id}` - Delete an alias
- `POST /api/v1/aliases/{alias_id}/test` - Test alias forwarding

### Activity and Logs

- `GET /api/v1/logs` - Get activity logs with optional filtering
- `GET /api/v1/stats` - Get account statistics

### Health Check

- `GET /api/v1/health` - API health check

## Features Implemented

### Security & Authentication

- Session-based authentication for all endpoints
- User authorization with ownership checks
- Proper HTTP status codes (401, 403, 404, etc.)
- Request validation using Pydantic models

### Request/Response Format

- JSON request bodies with Pydantic validation
- Consistent response format with `success` field
- Proper error handling with meaningful messages
- Standard REST HTTP methods (GET, POST, PATCH, DELETE)

### Data Models

- `DomainCreate` - For creating domains
- `DomainUpdate` - For updating domains
- `AliasCreate` - For creating aliases
- `AliasUpdate` - For updating aliases
- `AccountInfo` - For account information

### Functionality

- User-specific filtering (users only see their own data)
- Domain ownership validation
- Alias ownership validation
- DNS checking and validation
- Catch-all domain configuration
- Activity logging and statistics
- Alias expiration support
- Email forwarding testing

## Files Modified/Created

### New Files

- `views/api_view.py` - Comprehensive REST API implementation

### Modified Files

- `main.py` - Added API router registration
- `views/alias_view.py` - Fixed router prefix issue

## Usage Examples

### Create a Domain

```bash
curl -X POST http://localhost:8000/api/v1/domains \
  -H "Content-Type: application/json" \
  -d '{"name": "example.com", "catch_all": "admin@example.com"}' \
  --cookie "session=YOUR_SESSION"
```

### Create an Alias

```bash
curl -X POST http://localhost:8000/api/v1/domains/1/aliases \
  -H "Content-Type: application/json" \
  -d '{"local_part": "hello", "targets": "user@gmail.com"}' \
  --cookie "session=YOUR_SESSION"
```

### List User Domains

```bash
curl http://localhost:8000/api/v1/domains \
  --cookie "session=YOUR_SESSION"
```

### Get Account Info

```bash
curl http://localhost:8000/api/v1/account \
  --cookie "session=YOUR_SESSION"
```

## Notes

- All endpoints require authentication via session cookies
- Users can only access their own domains and aliases
- Admin users have the same access as regular users for these endpoints
- DNS checking functionality is integrated for domain validation
- Activity logging tracks all email forwarding activities
- The API follows RESTful conventions and HTTP standards