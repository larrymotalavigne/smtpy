# API Reference

## Domains
- `GET /api/domains` — List all domains
- `POST /api/domains` — Create a domain
- `GET /api/domains/{domain_id}` — Get a domain
- `DELETE /api/domains/{domain_id}` — Delete a domain

## Aliases
- `GET /api/aliases` — List all aliases
- `POST /api/aliases` — Create an alias
- `GET /api/aliases/{alias_id}` — Get an alias
- `DELETE /api/aliases/{alias_id}` — Delete an alias

## Example
```bash
curl -X POST http://localhost:8000/api/domains -H 'Content-Type: application/json' -d '{"name": "example.com", "catch_all": "user@gmail.com"}'
```

## Authentication
- (Planned) API key or token authentication for admin endpoints. 