# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive E2E test suite with Playwright (49 tests)
- Production Docker configurations with multi-stage builds
- CI/CD pipeline with GitHub Actions
- Database backup and restore scripts
- Disaster recovery documentation
- Deployment guides and production setup documentation
- Admin panel with system health monitoring
- Stripe billing integration with subscription management
- DKIM key generation for domains
- DNS auto-verification for domains
- Complete alias management system
- Real-time statistics with time-series charts
- Dashboard with metrics and charts

### Changed
- Upgraded to Angular 20 with standalone components
- Migrated to PrimeNG 20 components
- Updated to PostgreSQL 16+ for production
- Enhanced security with rate limiting and security headers
- Improved test infrastructure with 100% pass rate (99/99 tests)

### Fixed
- Billing API endpoint paths for Stripe integration
- Session management and authentication guard validation
- Authentication session handling with async SQLAlchemy
- Pydantic v2 field validators migration
- FastAPI deprecation warnings

### Security
- Implemented CSRF protection via session middleware
- Added security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- Rate limiting on authentication endpoints (10 req/min per IP)
- bcrypt password hashing with passlib
- HTTP-only session cookies

## [0.9.0] - 2025-11-05

### Added
- Initial project setup
- FastAPI backend with 3-layer architecture
- Angular frontend with modern UI
- PostgreSQL database with SQLAlchemy async
- User authentication system
- Domain management with DNS verification
- Email aliasing and forwarding
- SMTP server with aiosmtpd
- Message processing and statistics
- Comprehensive documentation

---

**Note**: This project is currently in active development. Version 1.0.0 will mark the first production-ready release.
