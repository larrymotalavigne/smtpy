1. [X] Replace all direct uses of request.app.TEMPLATES.TemplateResponse with config.template_response in views (user_view.py, billing_view.py, domain_view.py, and any others) to standardize rendering and ensure CSRF token injection and new TemplateResponse signature.
2. [X] Optionally add app.templates = SETTINGS.templates during app startup (create_app) to avoid attribute errors while migrating away from request.app.TEMPLATES usage; remove all remaining TEMPLATES references afterwards.
3. [X] Audit all HTML forms and ensure each includes a hidden input for csrf_token and that all POST endpoints call utils.csrf.validate_csrf; fix any missing validations.
4. [X] Unify environment variable naming: consistently use SMTPY_ENV across the codebase (replace stray SMTPY_ENVIRONMENT usage in config.validate_secret_key and ensure logging_config reads SMTPY_ENV consistently).
5. [X] Harmonize SMTP environment variables: choose SMTP_HOST/SMTP_PORT (per guidelines) and update forwarding/forwarder.py and docker-compose.dev.yml to use them (deprecate SMTP_RELAY).
6. [X] Add python-json-logger to pyproject.toml dependencies or make JSON logging optional in utils/logging_config.py to prevent runtime import errors in production.
7. [X] Review and modernize security headers in SecurityHeadersMiddleware: remove deprecated X-XSS-Protection, consider adding Permissions-Policy and Cross-Origin-Opener-Policy; update CSP to include Stripe domains used by billing.
8. [X] Ensure default admin credentials are not printed in production (guard create_default_admin logging/print statements with SETTINGS.is_development or equivalent).
9. [X] Centralize password hashing: use utils.user.hash_password (or a single CryptContext instance) everywhere; remove direct bcrypt.hash usage from views/main_view.py.
10. [X] Apply rate limiting to sensitive endpoints (login, registration, password reset, invite) using utils.rate_limit.check_rate_limit.
11. [ ] Replace ad-hoc request/session access to the current user with utils.user.require_login where appropriate to standardize redirect-to-login behavior.
12. [ ] Standardize template contexts to include a lightweight user mapping (from utils.user.get_current_user) where templates expect user fields; avoid passing ORM entities to templates.
13. [ ] Deduplicate functions in controllers/domain_controller.py (numerous repeated definitions) and controllers/main_controller.py (duplicate simple_* and *_sync variants). Keep a single canonical implementation per operation.
14. [ ] Use async for controller functions; if both are required, provide thin adapters that call the shared core logic to eliminate code duplication.
15. [ ] Enforce Pydantic request models for JSON API endpoints (e.g., alias add/delete, domain create) instead of dicts to validate input and improve OpenAPI docs.
16. [ ] Create custom exception classes in utils/error_handling.py for common error cases and ensure ErrorHandlingMiddleware maps them to proper HTTP responses.
17. [ ] Add indexes/constraints where appropriate: ensure (domain_id, local_part) is unique for alias, enforce email uniqueness if desired, and keep existing indexes validated.
18. [ ] Review soft deletion: ensure all queries for active records filter is_deleted == False; add a background task/management command to purge soft-deleted rows after retention period.
19. [ ] Review models for nullable fields and validation (e.g., User.email can be optional); define server-side defaults and constraints consistently.
20. [ ] Align Alembic migrations with current models; add an autogenerate workflow and instructions; create initial migration reflecting all indices and constraints.
21. [ ] Normalize database access in utils/db.py to read configuration from Settings (config.SETTINGS.DB_PATH) rather than environment variables directly.
22. [ ] Ensure tests patch both sync and async engines consistently; update fixtures if utils/db.py starts reading from Settings.
23. [ ] Expand test coverage for billing flows: create_checkout, create_billing_portal, and handle_webhook (happy path, invalid signature, subscription events).
24. [ ] Add unit tests for smtp_server/handler.py and forwarding/forwarder.py (including multipart, attachments, and error handling cases).
25. [ ] Add integration tests for alias lifecycle (create, list, forward email, delete) and domain DNS status endpoints.
26. [ ] Add tests for CSRF enforcement on all POST routes to ensure protection is applied and tokens are required when not in testing mode.
27. [ ] Add mypy type annotations to controllers and utils; enable mypy in CI with the stricter settings already present in pyproject.toml.
28. [ ] Enable Ruff and Black in pre-commit; add a .pre-commit-config.yaml and document setup in README.
29. [ ] Create GitHub Actions (or equivalent) CI workflow: uv sync, ruff/black/mypy, pytest with coverage; publish coverage artifacts.
30. [ ] Improve logging: include request ID/correlation ID middleware; add structured logging fields (user_id, endpoint) for security-relevant events; ensure privacy of sensitive data.
31. [ ] Surface activity logs in the admin UI with filtering by event_type, status, and time range; link logs to user/domain/alias where possible.
32. [ ] Implement DKIM signing in forwarding/forwarder.py using dkimpy based on configured domain keys; provide settings and docs in config_dns.
33. [ ] Add SPF/DKIM/DMARC verification helpers with caching in controllers/dns_controller.py; cache DNS lookups to reduce latency.
34. [ ] Improve SMTP error handling and retries in forwarding (e.g., exponential backoff, dead-letter queue or ActivityLog entries on failures).
35. [ ] Unify Stripe configuration: support both test and live keys (STRIPE_TEST_API_KEY, STRIPE_LIVE_API_KEY) and enforce live keys in production; sanitize webhook logging.
36. [ ] Validate STRIPE_BILLING_PORTAL_RETURN_URL against ALLOWED_HOSTS or a whitelist to prevent open redirects.
37. [ ] Ensure Content Security Policy allows Stripe JS and endpoints as needed on billing pages and blocks unsafe-inline where possible.
38. [ ] Review template inheritance and ensure templates/base.html sets common meta tags, CSP nonces if used, and CSRF in forms via a shared macro.
39. [ ] Replace any import aliasing patterns to adhere to guidelines (avoid `import x as y`), and standardize import order (ruff I/black formatting).
40. [ ] Remove the temporary views/web.py bridge (if present) and update Docker configs to use main:create_app --factory; clean up any references in docs.
41. [ ] Optimize Dockerfile: use multi-stage build, pin uv version, run as non-root user; cache uv sync effectively; reduce image size.
42. [ ] Fix docker-compose.dev.yml environment variables to match Settings (SMTPY_DB_PATH, SMTP_HOST, SMTP_PORT) and mount a named volume for the dev DB if desired.
43. [ ] Revisit pyproject.toml wheel build configuration: remove non-package directories (templates, static) from the packages list; include them as package data via hatch build data-files configuration.
44. [ ] Add caching headers for /static and consider fingerprinting assets; ensure StaticFiles mount sets appropriate cache-control in production.
45. [ ] Provide a management command or script to create an initial admin with a prompted password instead of printing credentials, for non-dev environments.
46. [ ] Implement password reset flows fully: generate signed, expiring tokens; create views to validate and update passwords; add email templates.
47. [ ] Harden session cookies: set same_site=strict for authenticated sessions if compatible; set secure=True in production; consider CSRF double-submit pattern.
48. [ ] Add health and readiness probes coverage: include DB connectivity, Stripe API health (optional), and SMTP relay checks; expose /livez and /readyz endpoints.
49. [ ] Document environment configuration in docs/config.md: provide a sample .env.example reflecting all settings and safe defaults.
50. [ ] Audit and remove dead code and TODO duplicates across controllers; break controllers/main_controller.py into smaller focused modules (auth, users, domains, billing) while keeping function-based style.
51. [ ] Add pagination to list endpoints (domains, aliases, activity logs) and update templates to support it.
52. [ ] Implement server-side input sanitization for email fields and domain names; add utils.validation helpers and apply them consistently.
53. [ ] Add a background cleaner to expire aliases automatically when expires_at is past; reflect status in UI.
54. [ ] Ensure all endpoints return consistent error messages and status codes; centralize in error handling utilities.
55. [ ] Add OpenAPI tags and descriptions for all endpoints; ensure FastAPI dependencies document security schemes used (session-based auth notes).
56. [ ] Create developer setup docs for uv (uv sync, uvicorn run variants), Docker (make build/run/logs), and testing (pytest commands) in README and docs/setup.md.
57. [ ] Add a CHANGELOG.md and versioning policy; wire project version from pyproject.toml into the app.
58. [ ] Implement feature flags (simple env-driven or settings-driven) for experimental features like DKIM signing or advanced DNS checks.
59. [ ] Add Guards for admin-only routes using a common dependency or decorator to centralize role checks instead of manual role != 'admin' checks.
60. [ ] Replace direct os.environ calls scattered in code (utils/db.py, forwarding/forwarder.py, utils/user.py) with reads from config.SETTINGS for consistency and testability.
61. [ ] Ensure tests cover template rendering paths after switching to config.template_response to catch regressions in CSRF/context injection.
62. [ ] Create centralized constants/enums (roles, subscription statuses, activity types) to avoid magic strings throughout the codebase.
63. [ ] Implement request validation for billing plan parameter (enum of allowed plans) and add server-side checks in controller.
64. [ ] Add graceful shutdown hooks for SMTP server (if running alongside API) and FastAPI app; ensure resources (DB, SMTP) close cleanly.
65. [ ] Introduce request timing and slow query logging to aid performance troubleshooting.
66. [ ] Add localization support scaffolding for templates (Jinja2 i18n) and keep user-facing strings ready for translation.
67. [ ] Establish code ownership and CODEOWNERS file to gate changes to security-sensitive areas (auth, billing, SMTP).
68. [ ] Review license and third-party notices; ensure compliance and include attribution where required.
69. [ ] Create a security.md with a responsible disclosure policy and high-level threat model overview for SMTPy.
