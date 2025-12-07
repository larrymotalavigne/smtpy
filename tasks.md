# SMTPy - Remaining Tasks & Feature Roadmap

**Project Status**: 98% Complete - Production Deployed at https://smtpy.fr

Last Updated: 2025-12-07

---

## 🎯 High Priority Tasks (Core Features)

### 1. User Preferences Storage
**Status**: Backend endpoints exist but return hardcoded data
**Impact**: High - Users cannot save notification preferences
**Effort**: Small (2-4 hours)

**Tasks**:
- [ ] Create `UserPreferences` database model with fields:
  - `user_id` (FK to User)
  - `email_notifications` (boolean)
  - `marketing_emails` (boolean)
  - `security_alerts` (boolean)
  - `weekly_reports` (boolean)
  - `theme` (string: light/dark/auto)
  - `language` (string)
- [ ] Add Alembic migration for preferences table
- [ ] Update `users_database.py` with CRUD functions
- [ ] Update `GET /users/preferences` to fetch from database
- [ ] Update `PUT /users/preferences` to persist to database
- [ ] Add unit tests for preferences storage
- [ ] Update frontend Settings page to use real preferences

**Files to modify**:
- `back/shared/models/` - Add `preferences.py` model
- `back/api/database/users_database.py` - Add preferences functions
- `back/api/views/users_view.py` - Update endpoints (lines 140-160)
- `back/migrations/versions/` - New migration

---

### 2. API Key Management
**Status**: Endpoints exist but return mock data
**Impact**: High - Required for programmatic API access
**Effort**: Medium (4-6 hours)

**Tasks**:
- [ ] Create `APIKey` database model with fields:
  - `id` (UUID)
  - `user_id` (FK to User)
  - `name` (string - user-defined key name)
  - `key_hash` (string - bcrypt hash of API key)
  - `prefix` (string - first 8 chars for identification)
  - `created_at` (datetime)
  - `last_used_at` (datetime, nullable)
  - `expires_at` (datetime, nullable)
  - `is_active` (boolean)
- [ ] Add Alembic migration for api_keys table
- [ ] Implement API key generation with secure random keys (e.g., `smtpy_sk_...`)
- [ ] Update `users_database.py` with API key CRUD functions
- [ ] Update `POST /users/api-keys` to generate and store keys
- [ ] Update `GET /users/api-keys` to list user's keys (hide full key)
- [ ] Update `DELETE /users/api-keys/{key_id}` to revoke keys
- [ ] Create authentication dependency to validate API keys
- [ ] Add API key authentication to protected endpoints (as alternative to sessions)
- [ ] Add unit tests for key generation, validation, and revocation
- [ ] Update frontend Settings page to show real API keys
- [ ] Add copy-to-clipboard functionality for new keys
- [ ] Show "last used" timestamp in UI

**Files to modify**:
- `back/shared/models/` - Add `api_key.py` model
- `back/api/database/users_database.py` - Add API key functions
- `back/api/views/users_view.py` - Update endpoints (lines 162-185)
- `back/api/core/dependencies.py` - Add API key auth dependency
- `front/src/app/pages/settings/settings.component.ts` - Connect to API
- `back/migrations/versions/` - New migration

---

### 3. Session Management & Tracking
**Status**: Endpoints exist but return empty data
**Impact**: Medium - Users cannot see or manage active sessions
**Effort**: Medium (4-6 hours)

**Tasks**:
- [ ] Create `Session` database model with fields:
  - `id` (UUID)
  - `user_id` (FK to User)
  - `token` (string - session token hash)
  - `device_info` (JSON - browser, OS, etc.)
  - `ip_address` (string)
  - `location` (string, nullable - city/country)
  - `created_at` (datetime)
  - `last_activity_at` (datetime)
  - `expires_at` (datetime)
  - `is_active` (boolean)
- [ ] Add Alembic migration for sessions table
- [ ] Update authentication middleware to track sessions on login
- [ ] Extract device info from User-Agent header
- [ ] Store IP address and location (optional, via GeoIP)
- [ ] Update session activity timestamp on each request
- [ ] Implement `GET /users/sessions` to list active sessions
- [ ] Implement `DELETE /users/sessions/{session_id}` to revoke single session
- [ ] Implement `DELETE /users/sessions` to revoke all sessions except current
- [ ] Add unit tests for session tracking and revocation
- [ ] Update frontend Settings page to show active sessions
- [ ] Add "Revoke" button per session in UI
- [ ] Add "Revoke all other sessions" button

**Files to modify**:
- `back/shared/models/` - Add `session.py` model
- `back/api/database/users_database.py` - Add session functions
- `back/api/views/auth_view.py` - Track sessions on login
- `back/api/views/users_view.py` - Update endpoints (lines 187-210)
- `back/shared/core/middlewares.py` - Update session activity
- `front/src/app/pages/settings/settings.component.ts` - Connect to API
- `back/migrations/versions/` - New migration

---

### 4. Message Size Tracking
**Status**: Field exists in model but not populated
**Impact**: Low - Nice-to-have for statistics
**Effort**: Small (1-2 hours)

**Tasks**:
- [ ] Update SMTP handler to calculate message size on receipt
- [ ] Store size in `Message.size_bytes` field (in `handler.py`)
- [ ] Update statistics view to show total size (remove TODO at line 122)
- [ ] Add size-based statistics (total GB forwarded, average size)
- [ ] Add unit tests for size calculation
- [ ] Display message size in frontend messages list
- [ ] Add size filter in messages search

**Files to modify**:
- `back/smtp_receiver/handler.py` - Calculate and store size
- `back/api/views/statistics_view.py` - Add size stats (line 122)
- `front/src/app/pages/messages/messages.component.ts` - Display size

---

### 5. Fix Catch-all Email Field Inconsistency
**Status**: Model uses `catch_all`, handler expects `catch_all_email`
**Impact**: High - Catch-all forwarding may be broken
**Effort**: Small (30 minutes)

**Tasks**:
- [ ] Review Domain model field name (currently `catch_all`)
- [ ] Review SMTP handler reference (currently `catch_all_email` at line 93)
- [ ] Standardize to single field name (recommend `catch_all_email`)
- [ ] Update model or handler to match
- [ ] Add migration if model changes
- [ ] Test catch-all forwarding functionality
- [ ] Add E2E test for catch-all email handling

**Files to check**:
- `back/shared/models/domain.py` - Current field name
- `back/smtp_receiver/handler.py` - Line 93 reference
- Add migration if needed

---

## 🔧 Medium Priority Tasks (Quality & Testing)

### 6. Fix Failing Backend Tests
**Status**: 3/99 tests failing (97% pass rate)
**Impact**: Medium - Should reach 100% pass rate
**Effort**: Small (2-3 hours)

**Tasks**:
- [ ] Run `pytest back/tests/ -v` to identify failing tests
- [ ] Fix each failing test
- [ ] Ensure all 99 tests pass
- [ ] Update CI/CD pipeline to require 100% pass rate

**Files to check**:
- `back/tests/` - All test files

---

### 7. Re-enable Disabled E2E Tests
**Status**: 13 E2E tests disabled across 3 spec files
**Impact**: Medium - Comprehensive test coverage needed
**Effort**: Medium (6-8 hours)

**Disabled Tests**:
- `e2e/auth.spec.ts` - 4 tests (landing page, dashboard, error handling, logout)
- `e2e/billing.spec.ts` - 8 tests (plan display, pricing, features, subscription, usage, upgrade, portal)
- `e2e/auth-simple.spec.ts` - 1 test (registration flow)

**Tasks**:
- [ ] Fix landing page navigation test
- [ ] Fix dashboard redirect test
- [ ] Fix auth error handling test
- [ ] Fix logout test
- [ ] Fix all 8 billing tests (plan display, pricing table, features, etc.)
- [ ] Fix registration flow test
- [ ] Ensure all Playwright tests pass
- [ ] Update CI/CD to run E2E tests on PRs

**Files to modify**:
- `front/e2e/auth.spec.ts` - Lines with `.skip` or `.fixme`
- `front/e2e/billing.spec.ts` - All disabled tests
- `front/e2e/auth-simple.spec.ts` - Registration test

---

## 🚀 Low Priority Tasks (Advanced Features)

### 8. Email Notifications System
**Status**: Not implemented
**Impact**: Medium - Users want notifications for failed forwards
**Effort**: Medium (6-8 hours)

**Tasks**:
- [ ] Create email templates for notifications:
  - Failed forward notification
  - Approaching quota warning
  - DNS verification status change
  - New device login alert
- [ ] Implement notification sending in controllers
- [ ] Add notification preferences (already in preferences model)
- [ ] Send email on message delivery failure
- [ ] Send email when quota reaches 80% and 90%
- [ ] Add notification history view in frontend
- [ ] Add unit tests for notification logic

**Files to create**:
- `back/api/templates/` - Email notification templates
- `back/api/controllers/notifications_controller.py` - New controller
- `front/src/app/pages/notifications/` - New page (optional)

---

### 9. Alias Notes & Labels
**Status**: Not implemented
**Impact**: Low - Quality of life improvement
**Effect**: Medium (4-6 hours)

**Tasks**:
- [ ] Add `notes` field to Alias model (text)
- [ ] Add `labels` or `tags` field to Alias model (array or separate table)
- [ ] Create migration
- [ ] Update alias CRUD endpoints to accept notes/labels
- [ ] Add notes textarea to alias creation/edit dialogs
- [ ] Add label/tag selector component
- [ ] Add label filtering in aliases list
- [ ] Add unit tests

**Files to modify**:
- `back/shared/models/alias.py` - Add fields
- `back/api/schemas/alias.py` - Update schemas
- `front/src/app/pages/aliases/aliases.component.ts` - Add UI

---

### 10. Two-Factor Authentication (2FA)
**Status**: Not implemented
**Impact**: Medium - Important security feature
**Effort**: Large (8-12 hours)

**Tasks**:
- [ ] Choose 2FA method (TOTP recommended - compatible with Google Authenticator, Authy)
- [ ] Add `totp_secret` field to User model (encrypted)
- [ ] Add `two_factor_enabled` boolean to User model
- [ ] Add `backup_codes` field (encrypted JSON array)
- [ ] Create migration
- [ ] Implement TOTP secret generation (using `pyotp` library)
- [ ] Create endpoints:
  - `POST /auth/2fa/enable` - Generate secret, return QR code
  - `POST /auth/2fa/verify` - Verify TOTP code and enable 2FA
  - `POST /auth/2fa/disable` - Disable 2FA (requires password + code)
  - `GET /auth/2fa/backup-codes` - Generate backup codes
  - `POST /auth/2fa/verify-backup-code` - Verify and consume backup code
- [ ] Update login flow to require TOTP after password
- [ ] Add 2FA setup wizard in Settings page
- [ ] Display backup codes after enabling 2FA
- [ ] Add QR code generation in frontend
- [ ] Add unit tests and E2E tests

**Files to modify**:
- `back/shared/models/user.py` - Add 2FA fields
- `back/api/views/auth_view.py` - Update login flow
- Add new `back/api/views/two_factor_view.py`
- `front/src/app/pages/settings/settings.component.ts` - Add 2FA section
- Add new `front/src/app/pages/auth/two-factor/` - 2FA verification page

---

### 11. Anonymous Reply
**Status**: Not implemented
**Impact**: High - Core privacy feature in competitors
**Effort**: Large (12-16 hours)

**Description**: Allow users to send emails FROM their aliases without revealing their real email address.

**Tasks**:
- [ ] Design reply architecture:
  - Dedicated SMTP server for outbound mail
  - Reply address format: `reply-{token}@smtpy.fr`
  - Token mapping: encrypted alias ID + recipient
- [ ] Add `reply_enabled` field to Alias model
- [ ] Create `Reply` tracking model:
  - `alias_id` (FK)
  - `original_sender` (email)
  - `reply_token` (encrypted)
  - `created_at`
  - `last_used_at`
- [ ] Implement outbound SMTP server
- [ ] Add reply token generation and encryption
- [ ] Update email forwarding to include Reply-To header
- [ ] Implement reply token validation and routing
- [ ] Add reply rate limiting
- [ ] Create reply UI in frontend (compose from alias)
- [ ] Add reply history view
- [ ] Add unit and E2E tests

**New files needed**:
- `back/smtp_sender/` - New outbound SMTP server
- `back/shared/models/reply.py` - Reply tracking model
- `front/src/app/pages/compose/` - Compose email page

---

### 12. Activity Audit Logs (Enhanced)
**Status**: Model exists but underutilized
**Impact**: Low - Useful for compliance and debugging
**Effort**: Medium (6-8 hours)

**Tasks**:
- [ ] Review existing ActivityLog model
- [ ] Add comprehensive logging to all controllers:
  - User login/logout
  - Password changes
  - API key creation/revocation
  - Alias creation/deletion
  - Domain verification
  - Billing changes
  - Settings updates
- [ ] Create activity log viewing endpoint (`GET /activity-logs`)
- [ ] Add filtering by action type, date range, user
- [ ] Create activity log viewer page in frontend
- [ ] Add export functionality (CSV)
- [ ] Add retention policy (auto-delete logs older than 90 days)

**Files to modify**:
- All controllers in `back/api/controllers/` - Add logging calls
- Add new `back/api/views/activity_logs_view.py`
- Add new `front/src/app/pages/activity/` - Activity log viewer

---

### 13. Email Forwarding Rules
**Status**: Not implemented
**Impact**: Medium - Advanced user feature
**Effort**: Large (10-14 hours)

**Description**: Allow users to create conditional forwarding rules (e.g., "forward emails from @company.com to work@email.com, block spam@*").

**Tasks**:
- [ ] Create `ForwardingRule` model:
  - `alias_id` (FK)
  - `priority` (integer for rule ordering)
  - `condition_type` (enum: SENDER_CONTAINS, SUBJECT_CONTAINS, SIZE_GREATER_THAN, etc.)
  - `condition_value` (string)
  - `action_type` (enum: FORWARD, BLOCK, REDIRECT)
  - `action_value` (string - email address for redirect)
  - `is_active` (boolean)
- [ ] Create migration
- [ ] Implement rule evaluation engine in SMTP handler
- [ ] Add rule CRUD endpoints
- [ ] Create rules UI in frontend (rule builder component)
- [ ] Add rule testing/preview functionality
- [ ] Add unit tests for rule evaluation

**New files**:
- `back/shared/models/forwarding_rule.py`
- `back/api/controllers/rules_controller.py`
- `back/api/database/rules_database.py`
- `back/api/views/rules_view.py`
- `front/src/app/pages/rules/` - Rule management page

---

### 14. PGP Encryption Support
**Status**: Not implemented
**Impact**: Low - Niche privacy feature
**Effort**: Large (14-20 hours)

**Description**: Encrypt forwarded emails with user's PGP public key.

**Tasks**:
- [ ] Add `pgp_public_key` field to User model (text)
- [ ] Create migration
- [ ] Integrate PGP library (e.g., `python-gnupg`)
- [ ] Implement email encryption in forwarding handler
- [ ] Add PGP key upload to Settings page
- [ ] Validate PGP key format on upload
- [ ] Add toggle to enable/disable PGP encryption per user
- [ ] Update email forwarding to encrypt when enabled
- [ ] Add unit tests for encryption

**Files to modify**:
- `back/shared/models/user.py` - Add PGP field
- `back/smtp_receiver/handler.py` - Encrypt before forwarding
- `front/src/app/pages/settings/settings.component.ts` - PGP key upload

---

### 15. Subdomain Support
**Status**: Not implemented
**Impact**: Medium - Popular feature in competitors
**Effort**: Large (12-16 hours)

**Description**: Allow users to create subdomains (e.g., `john.mydomain.com`) for better alias organization.

**Tasks**:
- [ ] Add `parent_domain_id` field to Domain model (self-referential FK)
- [ ] Add `is_subdomain` boolean to Domain model
- [ ] Create migration
- [ ] Update domain creation to support subdomains
- [ ] Validate subdomain format (DNS-safe)
- [ ] Update DNS verification to handle subdomains
- [ ] Add subdomain UI in domain creation dialog
- [ ] Show subdomain hierarchy in domains list
- [ ] Add subdomain filtering
- [ ] Add unit and E2E tests

**Files to modify**:
- `back/shared/models/domain.py` - Add subdomain fields
- `back/api/controllers/domains_controller.py` - Subdomain validation
- `front/src/app/pages/domains/domains.component.ts` - Subdomain UI

---

### 16. Team/Organization Collaboration
**Status**: Organization model exists but no multi-user support
**Impact**: Medium - Useful for businesses
**Effort**: Large (16-24 hours)

**Description**: Allow multiple users in an organization with role-based permissions.

**Tasks**:
- [ ] Create `OrganizationMember` model:
  - `organization_id` (FK)
  - `user_id` (FK)
  - `role` (enum: OWNER, ADMIN, MEMBER, VIEWER)
  - `joined_at`
  - `invited_by` (FK to User)
- [ ] Create `Invitation` model for pending invites
- [ ] Add role-based permissions system
- [ ] Create team management endpoints:
  - `POST /organizations/{org_id}/invite` - Invite user
  - `GET /organizations/{org_id}/members` - List members
  - `PATCH /organizations/{org_id}/members/{user_id}` - Update role
  - `DELETE /organizations/{org_id}/members/{user_id}` - Remove member
- [ ] Update authorization to check organization membership
- [ ] Create team management UI in frontend
- [ ] Add invitation acceptance flow
- [ ] Add unit and E2E tests

**New files**:
- `back/shared/models/organization_member.py`
- `back/shared/models/invitation.py`
- `back/api/controllers/teams_controller.py`
- `back/api/database/teams_database.py`
- `back/api/views/teams_view.py`
- `front/src/app/pages/team/` - Team management page

---

### 17. Webhooks Integration
**Status**: Not implemented
**Impact**: Low - Developer feature
**Effort**: Medium (8-12 hours)

**Description**: Allow users to configure webhooks for events (new message, failed forward, etc.).

**Tasks**:
- [ ] Create `Webhook` model:
  - `user_id` (FK)
  - `url` (string - target URL)
  - `events` (array - subscribed events)
  - `secret` (string - for signature verification)
  - `is_active` (boolean)
  - `last_triggered_at`
- [ ] Create migration
- [ ] Implement webhook delivery system (background task)
- [ ] Add HMAC signature generation
- [ ] Create webhook CRUD endpoints
- [ ] Add webhook testing endpoint (send test payload)
- [ ] Create webhooks UI in Settings page
- [ ] Add webhook delivery logs
- [ ] Add retry logic for failed deliveries
- [ ] Add unit tests

**New files**:
- `back/shared/models/webhook.py`
- `back/api/controllers/webhooks_controller.py`
- `back/api/database/webhooks_database.py`
- `back/api/services/webhook_service.py`
- Add to `back/api/views/webhooks_view.py` (already exists for Stripe)
- `front/src/app/pages/webhooks/` - Webhook management page

---

## 📋 Nice-to-Have Features (Future)

### 18. Import/Export User Data (GDPR)
- [ ] Implement data export (JSON format with all user data)
- [ ] Implement data import (restore from backup)
- [ ] Add GDPR-compliant data deletion
- [ ] Create export UI in Settings page

### 19. Mobile App (React Native or Flutter)
- [ ] Design mobile app architecture
- [ ] Implement authentication
- [ ] Implement core features (domains, aliases, messages)
- [ ] Add push notifications
- [ ] Publish to App Store and Google Play

### 20. Browser Extension
- [ ] Create browser extension (Chrome, Firefox, Safari)
- [ ] Add alias creation from context menu
- [ ] Add autofill integration
- [ ] Add quick alias generator

### 21. Custom Email Client (IMAP/POP3)
- [ ] Implement IMAP server
- [ ] Implement POP3 server
- [ ] Add mailbox feature (store emails instead of forwarding)
- [ ] Add spam filtering
- [ ] Add email search

### 22. White-Label Support
- [ ] Add customizable branding (logo, colors)
- [ ] Add custom domain for white-label deployments
- [ ] Add multi-tenancy support
- [ ] Create admin super-user for managing tenants

### 23. Social Login (OAuth)
- [ ] Add Google OAuth integration
- [ ] Add GitHub OAuth integration
- [ ] Add Microsoft OAuth integration
- [ ] Update login page with social login buttons

### 24. Real-time Notifications
- [ ] Implement WebSocket connection
- [ ] Add real-time message notifications
- [ ] Add real-time quota alerts
- [ ] Add notification bell icon in header

---

## 📊 Priority Matrix

| Priority | Category | Tasks | Estimated Effort |
|----------|----------|-------|------------------|
| **P0** (Critical) | Core Features | 1-5 | 10-15 hours |
| **P1** (High) | Quality & Testing | 6-7 | 8-11 hours |
| **P2** (Medium) | Advanced Features | 8-12 | 50-70 hours |
| **P3** (Low) | Advanced Features | 13-17 | 60-90 hours |
| **P4** (Future) | Nice-to-Have | 18-24 | 100+ hours |

---

## 🎯 Recommended Immediate Actions (Next Sprint)

1. **Fix Critical Issues** (2-3 days):
   - ✅ Fix catch-all email field inconsistency
   - ✅ Implement user preferences storage
   - ✅ Implement API key management
   - ✅ Fix failing backend tests

2. **Improve Test Coverage** (1-2 days):
   - ✅ Re-enable and fix all E2E tests
   - ✅ Achieve 100% backend test pass rate

3. **Complete Core Features** (2-3 days):
   - ✅ Implement session tracking
   - ✅ Add message size tracking
   - ✅ Add email notifications for failed forwards

4. **Polish & Documentation** (1 day):
   - ✅ Update README with complete feature list
   - ✅ Add API documentation examples
   - ✅ Create user guide

**Total Time to 100% Core Completion**: ~1-2 weeks

---

## 📝 Notes

- **Code Quality**: Maintain 3-layer architecture (views/controllers/database)
- **Testing**: Require unit tests for all new features
- **Security**: Review all features for security implications
- **Performance**: Monitor database query performance as features grow
- **UX**: Keep UI simple and intuitive, avoid feature bloat
- **Compatibility**: Ensure all features work with existing Stripe/DNS integrations

---

## 🔗 Related Documentation

- [README.md](../README.md) - Project overview and setup
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guidelines (TODO: create this)
- [API Documentation](http://localhost:8000/docs) - Swagger/OpenAPI docs
- [Deployment Guide](../docs/deployment.md) - Production deployment (TODO: create this)

---

**Last Review**: 2025-12-07
**Next Review**: After completing P0 tasks
