# Next Steps Roadmap - SMTPy Testing & Development

**Date**: October 24, 2025
**Current Status**: 100% test pass rate (99/99), 59% coverage
**Next Goal**: 70%+ coverage, SMTP tests, performance testing

---

## 🎯 Current Progress

### ✅ Completed (Session 1)
- [x] **100% test pass rate** (99/99 tests)
- [x] PostgreSQL testcontainers infrastructure
- [x] Professional-grade conftest.py (442 lines)
- [x] Test data fixtures (organization, domain, user)
- [x] Authenticated client fixture
- [x] 59% code coverage baseline
- [x] 7 comprehensive documentation files
- [x] Test runner script

### 🚧 In Progress (Session 2 - Started)
- [x] Analyzed low-coverage modules
- [x] Created billing controller test file (22 tests)
  - 10 tests passing
  - 12 tests need fixes (function signature mismatches)
- [ ] Fix billing controller tests
- [ ] Add statistics view tests
- [ ] Add domains controller tests

---

## 📋 Immediate Next Steps (1-2 hours)

### Step 1: Fix Billing Controller Tests
**File**: `back/tests/test_billing_controller.py`
**Current**: 10/22 passing
**Issue**: Function signature mismatches with actual controller

**Action Items**:
1. Read actual function signatures from `billing_controller.py`
2. Update test function calls to match signatures
3. Fix mock return values to match expected schemas
4. Verify all 22 tests pass

**Expected Outcome**: 22/22 billing tests passing

### Step 2: Measure Coverage Improvement
```bash
uv run python -m pytest back/tests/test_billing_controller.py --cov=back/api/controllers/billing_controller --cov-report=term
```

**Expected**: Billing controller coverage 19% → 50-60%

### Step 3: Add Remaining Coverage Tests
Add tests for uncovered code paths:
- Error handling branches
- Edge case scenarios
- Integration with database

**Expected**: Billing controller coverage 60% → 70%+

---

## 🗓️ Short-term Roadmap (This Week)

### Day 1: Complete Billing Controller Tests ✅
- [x] Created test file with 22 tests
- [ ] Fix 12 failing tests
- [ ] Achieve 70%+ coverage
- [ ] Document testing patterns

**Files**:
- `back/tests/test_billing_controller.py`

**Time Estimate**: 2-3 hours

### Day 2: Statistics View Tests
**Target**: 17% → 70% coverage

**Action Items**:
1. Create `test_statistics_controller.py`
2. Test all statistics endpoints:
   - `/statistics/overall`
   - `/statistics/time-series`
   - `/statistics/top-domains`
   - `/statistics/top-aliases`
3. Test edge cases:
   - Empty data sets
   - Date range boundaries
   - Invalid granularity
   - No domains/messages

**Expected Tests**: ~20-25 tests

**Time Estimate**: 3-4 hours

### Day 3: Domains Controller Tests
**Target**: 29% → 70% coverage

**Action Items**:
1. Create `test_domains_controller.py`
2. Test all domain operations:
   - Create domain
   - Verify domain (DNS checks)
   - Update domain
   - Delete domain
3. Test edge cases:
   - Duplicate domains
   - Invalid domain names
   - DNS verification failures
   - Missing organization

**Expected Tests**: ~15-20 tests

**Time Estimate**: 2-3 hours

### Day 4-5: Improve Other Low-Coverage Modules
**Targets**:
- `billing_database.py`: 35% → 70%
- `domains_database.py`: 38% → 70%
- `auth_view.py`: 51% → 70%

**Time Estimate**: 4-6 hours

---

## 🚀 Medium-term Roadmap (2-3 Weeks)

### Week 1: Coverage Improvements
- [x] Billing controller ✅
- [ ] Statistics view
- [ ] Domains controller
- [ ] Billing database
- [ ] Domains database
- [ ] Auth view

**Goal**: Achieve 70%+ overall coverage

### Week 2: SMTP Server Integration Tests
**Priority**: High
**Current Coverage**: 0%

**Action Items**:
1. **Create `test_smtp_integration.py`**
   - Email receiving tests
   - DKIM signing tests
   - SPF/DMARC validation
   - Forwarding logic tests

2. **Test Scenarios**:
   - Simple email forwarding
   - Email with attachments
   - HTML vs plain text
   - Large emails (size limits)
   - Invalid recipients
   - Bounce handling
   - Threading/conversations

3. **Mock Setup**:
   - Mock SMTP server for sending
   - Test SMTP server for receiving
   - DNS mocking for verification

**Expected Tests**: 30-40 tests

**Time Estimate**: 1 week (40 hours)

### Week 3: Performance Testing Setup
**Priority**: Medium
**Tools**: Locust or k6

**Action Items**:
1. **Install Locust**
   ```bash
   uv add --dev locust
   ```

2. **Create Performance Test Scenarios**:
   - `locustfiles/test_api_load.py`
   - `locustfiles/test_email_processing.py`
   - `locustfiles/test_concurrent_users.py`

3. **Test Scenarios**:
   - 100 concurrent users
   - 1000 emails/minute processing
   - API endpoint response times
   - Database connection pooling

4. **Establish Baselines**:
   - API response time targets (< 200ms p95)
   - Email processing throughput
   - Database query performance

**Expected Files**: 3-4 locustfiles

**Time Estimate**: 1 week (40 hours)

---

## 📊 Coverage Goals

### Current Coverage (59%)
```
High Coverage (>70%):
✅ models/*.py: 100%
✅ database/messages_database.py: 91%
✅ schemas/*: 89-94%

Medium Coverage (50-69%):
⚠️ database/users_database.py: 72%
⚠️ core/db.py: 68%
⚠️ controllers/messages_controller.py: 65%
⚠️ core/middlewares.py: 63%
⚠️ messages_view.py: 60%

Low Coverage (<50%):
❌ billing_controller.py: 19%
❌ statistics_view.py: 17%
❌ stripe_service.py: 26%
❌ domains_controller.py: 29%
❌ billing_database.py: 35%
❌ billing_view.py: 37%
❌ domains_database.py: 38%
❌ subscriptions_view.py: 43%
❌ domains_view.py: 44%
❌ auth_view.py: 51%
```

### Target Coverage (70%+)
**Priority Order**:
1. billing_controller.py: 19% → 70%+ ⏳ In Progress
2. statistics_view.py: 17% → 70%+
3. domains_controller.py: 29% → 70%+
4. billing_database.py: 35% → 70%+
5. domains_database.py: 38% → 70%+
6. Other <70% modules

**Time Estimate**: 2-3 weeks to reach 70% overall

---

## 🎓 Testing Patterns Established

### Pattern 1: Controller Tests with Mocks
```python
@pytest.mark.asyncio
class TestControllerFunction:
    async def test_success_case(self, async_db, test_organization):
        with patch('api.services.external_service') as mock_service:
            mock_service.return_value = {"data": "value"}

            result = await controller.function(db=async_db, org_id=1)

            assert result is not None
            mock_service.assert_called_once()

    async def test_error_case(self, async_db):
        with pytest.raises(ValueError, match="Expected error"):
            await controller.function(db=async_db, org_id=99999)
```

### Pattern 2: Edge Case Coverage
Test ALL paths:
- ✅ Success case
- ✅ Not found case
- ✅ Invalid input case
- ✅ External service failure case
- ✅ Database error case
- ✅ Permission denied case

### Pattern 3: Database Integration
```python
async def test_with_real_data(self, async_db, test_organization, test_domain):
    # Uses real database with fixtures
    # Tests actual data relationships
    # Verifies FK constraints
```

---

## 📈 Success Metrics

### Test Metrics
- ✅ Pass Rate: 100% (99/99)
- 🎯 Coverage: 59% → 70%+ (target)
- 🎯 Total Tests: 99 → 150+ (target)
- 🎯 Test Files: 9 → 15+ (target)

### Quality Metrics
- ✅ All dependencies fixed
- ✅ All deprecations fixed
- ✅ Professional test infrastructure
- 🎯 SMTP server tested
- 🎯 Performance baselines established

### Documentation Metrics
- ✅ 7 comprehensive docs created
- ✅ Test patterns documented
- ✅ Quick reference guides
- 🎯 Performance testing docs
- 🎯 SMTP testing docs

---

## 🛠️ Quick Reference

### Run Tests
```bash
# All tests
./scripts/run-tests.sh

# With coverage
./scripts/run-tests.sh --coverage

# Specific module coverage
uv run python -m pytest back/tests/test_billing_controller.py \
  --cov=back/api/controllers/billing_controller \
  --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Create New Test File
```bash
# Use billing controller test as template
cp back/tests/test_billing_controller.py \
   back/tests/test_statistics_controller.py

# Update imports and test cases
```

### Check Coverage
```bash
# Full coverage report
uv run python -m pytest back/tests/ \
  --cov=back/api \
  --cov-report=html \
  --cov-report=term

# Module-specific coverage
uv run python -m pytest back/tests/ \
  --cov=back/api/controllers \
  --cov-report=term
```

---

## 🎯 Next Session Goals

### Immediate (Next 2 hours)
1. Fix billing controller test failures (12 tests)
2. Verify 70%+ billing controller coverage
3. Document billing test patterns

### Short-term (Next week)
1. Complete statistics view tests (17% → 70%)
2. Complete domains controller tests (29% → 70%)
3. Reach 65%+ overall coverage

### Medium-term (Next 2-3 weeks)
1. Complete all <70% module tests
2. Add SMTP server integration tests
3. Set up performance testing framework
4. Reach 70%+ overall coverage

---

## 📞 Support & Resources

### Documentation
- **Testing Analysis**: `docs/testing-analysis.md`
- **Testing Complete**: `docs/TESTING_COMPLETE.md`
- **100% Achievement**: `docs/100-percent-achievement.md`
- **This Roadmap**: `docs/NEXT_STEPS_ROADMAP.md`

### Test Templates
- **Billing Controller**: `back/tests/test_billing_controller.py` (use as template)
- **conftest.py**: `back/tests/conftest.py` (fixtures reference)

### Commands
- **Test Runner**: `./scripts/run-tests.sh --help`
- **Coverage Report**: `open htmlcov/index.html`

---

## ✅ Completion Checklist

### Phase 1: Test Infrastructure ✅
- [x] 100% test pass rate
- [x] PostgreSQL testcontainers
- [x] Professional fixtures
- [x] Coverage reporting
- [x] Documentation

### Phase 2: Coverage Improvements 🚧
- [x] Billing controller tests created (10/22 passing)
- [ ] Billing controller tests fixed
- [ ] Statistics view tests
- [ ] Domains controller tests
- [ ] 70%+ overall coverage

### Phase 3: SMTP Testing ⏳
- [ ] SMTP integration tests
- [ ] Email forwarding tests
- [ ] DKIM/SPF/DMARC tests
- [ ] Bounce handling tests

### Phase 4: Performance Testing ⏳
- [ ] Locust/k6 setup
- [ ] Load test scenarios
- [ ] Performance baselines
- [ ] Continuous monitoring

---

**Last Updated**: October 24, 2025
**Status**: Phase 1 Complete, Phase 2 In Progress
**Next Milestone**: 70% Coverage + SMTP Tests

🚀 **Ready to continue improving test coverage and adding SMTP integration tests!**
