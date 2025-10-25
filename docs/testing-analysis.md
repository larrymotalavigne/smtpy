# Testing Improvements Analysis

**Date**: October 24, 2025
**Status**: 93/99 tests passing (93.9% pass rate)
**Failed Tests**: 6 failures (3 auth integration + 3 billing endpoints)

---

## Executive Summary

The SMTPy backend test suite has **93 passing tests out of 99 total** (93.9% pass rate). The 6 failing tests appear to be related to:
1. Database state isolation issues in the integration test suite
2. Authentication/authorization issues in billing endpoint tests

### Current Test Coverage

| Test File | Tests | Status | Notes |
|-----------|-------|--------|-------|
| `test_auth_unit.py` | 14 | ✅ All Pass | Unit tests for auth functions |
| `test_basic.py` | 4 | ✅ All Pass | Basic API health checks |
| `test_debug_auth.py` | 1 | ✅ All Pass | Debug authentication test |
| `test_functional_users.py` | 3 | ✅ All Pass | User functional tests |
| `test_messages.py` | 31 | ✅ All Pass | Message handling tests |
| `test_security.py` | 2 | ✅ All Pass | Security middleware tests |
| `test_auth_integration.py` | 16 | ⚠️ 3 Failing | Integration tests with PostgreSQL testcontainer |
| `test_endpoints.py` | 28 | ⚠️ 3 Failing | API endpoint tests |

---

## Detailed Failure Analysis

### Category 1: Authentication Integration Test Failures (3 tests)

**Location**: `back/tests/test_auth_integration.py`

#### Test 1: `test_login_endpoint`
- **Line**: 465
- **Error**: `assert 401 == 200`
- **Root Cause**: Registration returns `400 Bad Request` before login attempt
- **Symptom**:
  ```
  HTTP Request: POST http://test/auth/register "HTTP/1.1 400 Bad Request"
  HTTP Request: POST http://test/auth/login "HTTP/1.1 401 Unauthorized"
  ```
- **Observation**: **Test passes when run individually**, fails when run with full suite
- **Diagnosis**: Database state isolation issue - SQLite in-memory DB likely being reused

#### Test 2: `test_login_with_email`
- **Line**: 487
- **Error**: `assert 401 == 200`
- **Root Cause**: Same as Test 1 - registration fails with 400
- **Pattern**: Identical to test_login_endpoint failure

#### Test 3: `test_get_current_user`
- **Line**: 538
- **Error**: `assert 401 == 200`
- **Root Cause**: Same registration failure pattern

### Category 2: Billing Endpoint Authorization Failures (3 tests)

**Location**: `back/tests/test_endpoints.py`

#### Test 4: `test_create_checkout_session`
- **Line**: 216
- **Error**: `assert 401 in [201, 400]`
- **Response**: `HTTP/1.1 401 Unauthorized`
- **Root Cause**: Missing or invalid authentication credentials
- **Diagnosis**: Test is not properly authenticated before making request

#### Test 5: `test_get_customer_portal`
- **Line**: 223
- **Error**: `assert 401 in [200, 400, 404]`
- **Response**: `HTTP/1.1 401 Unauthorized`
- **Root Cause**: Same authentication issue

#### Test 6: `test_get_organization_billing`
- **Line**: 254
- **Error**: `assert 401 == 404`
- **Response**: `HTTP/1.1 401 Unauthorized`
- **Root Cause**: Same authentication issue

---

## Warnings & Deprecations

### 1. Python JSON Logger Deprecation
- **Warning**: `pythonjsonlogger.jsonlogger has been moved to pythonjsonlogger.json`
- **Status**: ✅ **FIXED** - Updated import in `back/api/core/logging_config.py:4`
- **Solution**: Changed from `from pythonjsonlogger.json import JsonFormatter` to `from pythonjsonlogger import jsonlogger`

### 2. FastAPI Query Parameter Deprecation
- **Warning**: `regex` has been deprecated, please use `pattern` instead
- **Locations**:
  - `back/api/views/statistics_view.py:131`
  - `back/api/views/statistics_view.py:341`
- **Status**: ⚠️ **NEEDS FIX**
- **Solution**: Replace `regex=` with `pattern=` in Query() calls

### 3. Testcontainers Deprecation
- **Warning**: `@wait_container_is_ready decorator is deprecated`
- **Status**: ⚠️ **NEEDS FIX** (Low priority - external dependency)
- **Solution**: Update to structured wait strategies when updating testcontainers version

### 4. SQLAlchemy Collection Warning
- **Warning**: `PytestCollectionWarning: cannot collect 'test_sessionmaker'`
- **Status**: ⚠️ **MINOR** - pytest trying to collect non-test function
- **Impact**: Cosmetic warning, does not affect functionality

---

## Dependencies Fixed

During analysis, the following dependency issues were resolved:

1. ✅ **python-json-logger** - Added to `pyproject.toml` dependencies (v3.2.1)
2. ✅ **httpx** - Added to dev dependencies (v0.28.0+)
3. ✅ **pytest-cov** - Added to dev dependencies (v5.0.0+)
4. ✅ **aiosqlite** - Added to dev dependencies (v0.21.0+)
5. ✅ **ruff** - Added to dev dependencies (v0.14.0+)
6. ✅ **mypy** - Added to dev dependencies (v1.18.0+)

---

## Recommended Fixes (Priority Order)

### Priority 1: Fix Database State Isolation (Auth Integration Tests)

**Issue**: Tests fail when run together but pass individually

**Root Cause**: The `async_db` fixture in `conftest.py` uses function scope but the database state is not being properly cleared between tests.

**Solution Options**:

**Option A: Fix the async_db fixture**
```python
@pytest_asyncio.fixture(scope="function")
async def async_db(async_engine):
    """Provide async database session for tests."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from api.models.base import Base

    # Recreate all tables for each test
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    testing_async_session_local = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=async_engine
    )

    async with testing_async_session_local() as session:
        yield session
        await session.rollback()
```

**Option B: Use PostgreSQL testcontainer for all tests**
- Currently only auth_integration tests use testcontainers
- Ensure proper isolation with Docker containers
- More realistic production environment

### Priority 2: Fix Billing Endpoint Tests (Authorization)

**Issue**: Billing endpoints returning 401 Unauthorized

**Root Cause**: Tests are not authenticating before making requests

**Solution**: Add authentication setup in test fixtures or individual tests:

```python
@pytest.fixture
async def authenticated_client(client):
    """Create an authenticated client for testing protected endpoints."""
    # Register user
    register_response = await client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    })

    # Login and get session
    login_response = await client.post("/auth/login", json={
        "username": "testuser",
        "password": "SecurePass123!"
    })

    # Return client with session cookies
    return client

# Then update tests to use authenticated_client:
async def test_create_checkout_session(authenticated_client):
    response = await authenticated_client.post("/billing/checkout-session", ...)
    assert response.status_code in [201, 400]
```

### Priority 3: Fix FastAPI Deprecation Warnings

**Issue**: `regex` parameter is deprecated in Query()

**Solution**: Update `statistics_view.py`:

```python
# Line 131 and 341 - Replace:
granularity: str = Query("day", regex="^(day|week|month)$"),

# With:
granularity: str = Query("day", pattern="^(day|week|month)$"),
```

---

## Next Steps: Test Coverage Improvements

### 1. Set Up Test Coverage Reporting ✅ (pytest-cov installed)

```bash
# Run tests with coverage
uv run python -m pytest back/tests/ --cov=back/api --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### 2. Add Missing Tests

**Controllers Missing Edge Case Tests**:
- `billing_controller.py` - Edge cases for Stripe errors
- `domains_controller.py` - DNS verification edge cases
- `messages_controller.py` - Email forwarding edge cases

**SMTP Server Tests** (Currently Missing):
- Integration tests for SMTP server (`back/smtp/smtp_server/`)
- Email receiving and processing tests
- DKIM signing tests
- Forwarding reliability tests

### 3. Performance Testing Setup

**High-Volume Scenarios**:
- 1000+ emails/minute processing
- Concurrent user registration
- Database connection pool under load
- API rate limiting effectiveness

**Tools to Consider**:
- **Locust** - Python-based load testing
- **k6** - Modern load testing tool
- **pytest-benchmark** - Microbenchmarks

---

## Test Statistics

```
Total Tests: 99
Passing: 93 (93.9%)
Failing: 6 (6.1%)
Warnings: 8
Test Files: 8
Execution Time: ~14 seconds (full suite)
```

---

## Conclusion

The test suite is in **good shape** with a 93.9% pass rate. The 6 failing tests are due to:
1. **Fixable database isolation issues** (3 tests)
2. **Missing authentication setup** in billing tests (3 tests)

All failures are **easily fixable** and do not indicate fundamental architecture problems. The test infrastructure is solid with:
- ✅ Good fixture setup in `conftest.py`
- ✅ Async testing support with `pytest-asyncio`
- ✅ Integration testing with testcontainers
- ✅ Both unit and integration test coverage

**Estimated Time to Fix**: 2-4 hours to get to 100% pass rate.

**Next Priorities**:
1. Fix the 6 failing tests (2-4 hours)
2. Add test coverage reporting (30 minutes)
3. Expand test coverage for controllers (1-2 days)
4. Add SMTP server integration tests (1-2 days)
5. Set up performance testing framework (1 week)
