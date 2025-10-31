# SMTPy Testing Roadmap - Quality-First Approach

**Status**: Week 1-2 Sprint Started
**Goal**: Achieve comprehensive test coverage before production launch
**Timeline**: 4 weeks to production-ready quality

---

## 📊 Current Testing Status

### E2E Tests (Playwright)
- **Status**: ✅ Configured and running
- **Current**: 49 tests
- **Pass Rate**: Checking...
- **Coverage**: Authentication, Dashboard, Domains, Messages, Billing, Navigation
- **Gap**: Registration flow, Password reset, Email verification, Domain DNS verification

### Frontend Unit Tests
- **Status**: ⚠️ Minimal coverage
- **Current**: 7 tests
- **Components**: 13 pages created, minimal tests
- **Services**: 12 services created, no tests
- **Target**: 80% coverage

### Backend Integration Tests
- **Status**: ⚠️ Near complete
- **Current**: 97/99 tests passing (97% pass rate)
- **Coverage**: 59% baseline
- **Gaps**: 2 failing tests, SMTP server tests, edge cases
- **Target**: 100% pass rate, 90% coverage

---

## 🎯 Week 1-2: Comprehensive Testing Sprint

### Week 1: E2E & Frontend Tests

#### Day 1-2: E2E Test Stabilization
**Objective**: Get all 49 existing tests passing consistently

**Tasks**:
- [x] Run full E2E test suite
- [ ] Fix any failing tests
- [ ] Add test retry logic for flaky tests
- [ ] Document test credentials and setup
- [ ] Verify CI/CD pipeline runs E2E tests successfully

**Deliverable**: All 49 E2E tests passing with <5% flakiness

---

#### Day 3-5: E2E Test Expansion
**Objective**: Add critical missing user flows

**Priority 1 - Authentication Flows**:
```typescript
// tests/auth-flows.spec.ts
describe('User Registration Flow', () => {
  test('should complete full registration flow', async ({ page }) => {
    // 1. Navigate to register page
    // 2. Fill registration form
    // 3. Submit and verify email sent message
    // 4. (Mock) Click email verification link
    // 5. Verify account activated
    // 6. Login with new credentials
  });

  test('should handle duplicate email registration', async ({ page }) => {
    // Test duplicate email error
  });
});

describe('Password Reset Flow', () => {
  test('should complete password reset', async ({ page }) => {
    // 1. Request password reset
    // 2. Verify email sent
    // 3. (Mock) Click reset link
    // 4. Set new password
    // 5. Login with new password
  });

  test('should reject expired reset tokens', async ({ page }) => {
    // Test token expiration
  });
});
```

**Priority 2 - Domain Management Flow**:
```typescript
// tests/domain-management.spec.ts
describe('Domain Complete Flow', () => {
  test('should complete domain creation and verification', async ({ page }) => {
    // 1. Login
    // 2. Navigate to domains
    // 3. Add new domain
    // 4. View DNS configuration instructions
    // 5. (Mock) Verify DNS records
    // 6. See domain status change to verified
    // 7. Create alias on verified domain
    // 8. Test email forwarding (mock)
  });

  test('should handle domain verification failure', async ({ page }) => {
    // Test DNS verification failure cases
  });
});
```

**Priority 3 - Email Forwarding Flow**:
```typescript
// tests/email-forwarding.spec.ts
describe('Email Processing Flow', () => {
  test('should receive and forward email', async ({ page }) => {
    // 1. Set up domain and alias
    // 2. (Mock) Send test email to alias
    // 3. Verify email appears in messages list
    // 4. Verify email forwarded to destination
    // 5. Check message statistics updated
  });

  test('should handle bounced emails', async ({ page }) => {
    // Test bounce handling
  });
});
```

**Deliverable**: 15-20 new E2E tests covering critical flows

---

#### Day 6-10: Frontend Unit Tests

**Objective**: Expand from 7 to 100+ unit tests

**Phase 1: Component Tests** (Target: 50 tests)

Create test files for all 13 pages:
```bash
front/src/app/pages/
├── auth/
│   ├── login.component.spec.ts          # 5 tests
│   ├── register.component.spec.ts       # 5 tests
│   └── reset-password.component.spec.ts # 4 tests
├── dashboard/
│   └── dashboard.component.spec.ts      # 8 tests (charts, metrics)
├── domains/
│   ├── domains-list.component.spec.ts   # 6 tests
│   └── domain-detail.component.spec.ts  # 5 tests
├── messages/
│   ├── messages-list.component.spec.ts  # 6 tests
│   └── message-detail.component.spec.ts # 4 tests
├── billing/
│   └── billing.component.spec.ts        # 5 tests
├── profile/
│   └── profile.component.spec.ts        # 4 tests
└── statistics/
    └── statistics.component.spec.ts     # 6 tests
```

**Component Test Template**:
```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ComponentName } from './component-name.component';
import { ServiceName } from '../../services/service-name.service';
import { of, throwError } from 'rxjs';

describe('ComponentName', () => {
  let component: ComponentName;
  let fixture: ComponentFixture<ComponentName>;
  let mockService: jasmine.SpyObj<ServiceName>;

  beforeEach(async () => {
    mockService = jasmine.createSpyObj('ServiceName', ['method1', 'method2']);

    await TestBed.configureTestingModule({
      imports: [ComponentName],
      providers: [
        { provide: ServiceName, useValue: mockService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ComponentName);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load data on init', () => {
    const mockData = { /* mock data */ };
    mockService.method1.and.returnValue(of(mockData));

    fixture.detectChanges(); // triggers ngOnInit

    expect(component.data).toEqual(mockData);
    expect(mockService.method1).toHaveBeenCalled();
  });

  it('should handle errors gracefully', () => {
    mockService.method1.and.returnValue(throwError(() => new Error('Test error')));

    fixture.detectChanges();

    expect(component.error).toBeTruthy();
    expect(component.loading).toBeFalsy();
  });

  // Add more specific tests for component logic
});
```

**Phase 2: Service Tests** (Target: 36 tests - 3 per service)

Test all 12 services:
```bash
front/src/app/services/
├── auth.service.spec.ts          # 5 tests
├── domain.service.spec.ts        # 4 tests
├── message.service.spec.ts       # 4 tests
├── statistics.service.spec.ts    # 3 tests
├── billing.service.spec.ts       # 4 tests
├── user.service.spec.ts          # 3 tests
├── api.service.spec.ts           # 3 tests
├── toast.service.spec.ts         # 2 tests
├── loading.service.spec.ts       # 2 tests
├── theme.service.spec.ts         # 2 tests
└── ... (other services)
```

**Service Test Template**:
```typescript
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ServiceName } from './service-name.service';

describe('ServiceName', () => {
  let service: ServiceName;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ServiceName]
    });

    service = TestBed.inject(ServiceName);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify(); // Ensure no outstanding requests
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch data from API', () => {
    const mockData = { /* mock response */ };

    service.getData().subscribe(data => {
      expect(data).toEqual(mockData);
    });

    const req = httpMock.expectOne('/api/endpoint');
    expect(req.request.method).toBe('GET');
    req.flush(mockData);
  });

  it('should handle HTTP errors', () => {
    service.getData().subscribe({
      next: () => fail('should have failed'),
      error: (error) => {
        expect(error.status).toBe(500);
      }
    });

    const req = httpMock.expectOne('/api/endpoint');
    req.flush('Error', { status: 500, statusText: 'Server Error' });
  });
});
```

**Phase 3: Guard & Interceptor Tests** (Target: 10 tests)

**Deliverable**: 100+ frontend unit tests, 80% code coverage

---

### Week 2: Backend & Integration Tests

#### Day 11-13: Backend Test Fixes
**Objective**: Achieve 100% pass rate (99/99 tests)

**Tasks**:
- [ ] Identify the 2 failing tests
- [ ] Debug and fix root causes
- [ ] Add edge case tests for all controllers
- [ ] Increase coverage from 59% to 75%

**Failing Tests Investigation**:
```bash
# Run tests with verbose output
cd back
uv run pytest -v --tb=short

# Run specific failing tests
uv run pytest tests/path/to/failing_test.py -v

# Check coverage
uv run pytest --cov=. --cov-report=html
```

**Add Edge Case Tests**:
```python
# tests/test_domain_controller_edge_cases.py
def test_domain_with_invalid_dns():
    """Test domain creation with malformed DNS records"""
    pass

def test_domain_deletion_with_active_aliases():
    """Test domain deletion when aliases exist"""
    pass

def test_concurrent_domain_verification():
    """Test race conditions in DNS verification"""
    pass
```

**Deliverable**: 99/99 tests passing, 75% coverage

---

#### Day 14-16: SMTP Server Integration Tests
**Objective**: Add comprehensive SMTP server testing

**New Test File**: `tests/integration/test_smtp_server.py`

```python
import asyncio
import smtplib
from email.mime.text import MIMEText
import pytest

@pytest.mark.asyncio
async def test_smtp_server_receives_email():
    """Test SMTP server receives and processes email"""
    # 1. Start SMTP server
    # 2. Send test email via smtplib
    # 3. Verify email received
    # 4. Check database for message record
    pass

@pytest.mark.asyncio
async def test_smtp_dkim_signing():
    """Test DKIM signature is added to outgoing emails"""
    pass

@pytest.mark.asyncio
async def test_smtp_email_forwarding():
    """Test end-to-end email forwarding"""
    pass

@pytest.mark.asyncio
async def test_smtp_bounce_handling():
    """Test bounce email processing"""
    pass

@pytest.mark.asyncio
async def test_smtp_spam_detection():
    """Test spam filtering if implemented"""
    pass

@pytest.mark.asyncio
async def test_smtp_rate_limiting():
    """Test email rate limiting per domain"""
    pass

@pytest.mark.asyncio
async def test_smtp_concurrent_connections():
    """Test multiple concurrent SMTP connections"""
    pass
```

**Deliverable**: 10+ SMTP integration tests

---

#### Day 17-20: Load & Performance Testing
**Objective**: Set up load testing and identify bottlenecks

**Install k6**:
```bash
# macOS
brew install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Create Load Tests**:

**Test 1: API Endpoint Performance** (`tests/load/api-load-test.js`)
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% of requests < 200ms
    http_req_failed: ['rate<0.01'],     // Error rate < 1%
  },
};

export default function () {
  // Test login
  const loginRes = http.post('http://localhost:8000/auth/login', {
    username: 'testuser',
    password: 'testpass'
  });

  check(loginRes, {
    'login successful': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  // Test dashboard
  const dashboardRes = http.get('http://localhost:8000/dashboard');
  check(dashboardRes, {
    'dashboard loaded': (r) => r.status === 200,
  });

  sleep(1);
}
```

**Test 2: Email Processing Performance** (`tests/load/smtp-load-test.js`)
```javascript
import { SMTPClient } from 'k6/x/smtp';
import { check } from 'k6';

export const options = {
  vus: 50,  // 50 concurrent email senders
  duration: '5m',
  thresholds: {
    'smtp_send_duration': ['p(95)<1000'],  // 95% of emails sent < 1s
  },
};

export default function () {
  const client = new SMTPClient({
    host: 'localhost',
    port: 1025,
  });

  const res = client.send({
    from: 'test@example.com',
    to: 'alias@yourdomain.com',
    subject: 'Load Test Email',
    body: 'This is a load test email',
  });

  check(res, {
    'email sent': (r) => r.success === true,
  });
}
```

**Test 3: Database Query Performance** (`tests/load/db-load-test.js`)
```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 100,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<100'],  // 95% of queries < 100ms
  },
};

export default function () {
  // Test high-frequency queries
  const messagesRes = http.get('http://localhost:8000/messages?limit=20');
  check(messagesRes, {
    'messages query fast': (r) => r.timings.duration < 100,
  });

  const domainsRes = http.get('http://localhost:8000/domains');
  check(domainsRes, {
    'domains query fast': (r) => r.timings.duration < 50,
  });
}
```

**Run Load Tests**:
```bash
# Run individual tests
k6 run tests/load/api-load-test.js
k6 run tests/load/smtp-load-test.js
k6 run tests/load/db-load-test.js

# Run with output to InfluxDB + Grafana (optional)
k6 run --out influxdb=http://localhost:8086/k6 tests/load/api-load-test.js
```

**Deliverable**: Load test suite with performance baselines documented

---

## 🔐 Week 3-4: Security & Performance

### Week 3: Security Testing

#### Day 21-23: Security Audit
**Objective**: Identify and fix security vulnerabilities

**Tools**:
1. **OWASP ZAP** (Web Application Security Scanner)
2. **npm audit** (Frontend dependencies)
3. **pip-audit** (Backend dependencies)
4. **Bandit** (Python security linter)

**Tasks**:

**1. Dependency Security Audit**:
```bash
# Frontend
cd front
npm audit
npm audit fix

# Backend
cd back
pip install pip-audit
pip-audit

# Fix critical and high vulnerabilities
```

**2. OWASP ZAP Automated Scan**:
```bash
# Install OWASP ZAP
# https://www.zaproxy.org/download/

# Run automated scan
zap.sh -cmd -quickurl http://localhost:4200 -quickout zap-report.html

# Or use Docker
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:4200
```

**3. Manual Security Testing Checklist**:
```markdown
### Authentication & Session Management
- [ ] Test SQL injection in login form
- [ ] Test XSS in all input fields
- [ ] Test CSRF protection on state-changing operations
- [ ] Verify session timeout works
- [ ] Test session fixation attacks
- [ ] Verify password hashing (bcrypt)
- [ ] Test brute force protection

### API Security
- [ ] Test unauthorized API access
- [ ] Test parameter tampering
- [ ] Test mass assignment vulnerabilities
- [ ] Verify rate limiting works
- [ ] Test CORS configuration
- [ ] Verify sensitive data not in URLs/logs

### Email Security
- [ ] Test email header injection
- [ ] Test DKIM signature validation
- [ ] Verify SPF/DMARC configuration
- [ ] Test for email bombing protection

### Infrastructure
- [ ] Verify HTTPS enforcement
- [ ] Check security headers (CSP, HSTS, etc.)
- [ ] Verify secrets not in code/logs
- [ ] Test file upload vulnerabilities (if any)
- [ ] Verify database access controls
```

**4. Code Security Review**:
```bash
# Python security linting
pip install bandit
bandit -r back/ -ll

# Check for hardcoded secrets
pip install detect-secrets
detect-secrets scan
```

**Deliverable**: Security audit report with all critical/high issues fixed

---

#### Day 24-26: Performance Optimization
**Objective**: Optimize based on load test results

**Backend Optimizations**:

**1. Database Query Optimization**:
```python
# Add indexes for common queries
# back/alembic/versions/004_add_performance_indexes.py

def upgrade():
    # Add index on messages.created_at for time-based queries
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])

    # Add composite index for user messages
    op.create_index('idx_messages_user_created', 'messages', ['user_id', 'created_at'])

    # Add index on domains.verified for filtering
    op.create_index('idx_domains_verified', 'domains', ['verified'])
```

**2. Add Redis Caching**:
```python
# back/api/cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(ttl=300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"{func.__name__}:{hash(str(args))}{hash(str(kwargs))}"

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage in controllers
@cache_result(ttl=60)  # Cache for 60 seconds
async def get_dashboard_stats(user_id: int):
    # Expensive database query
    pass
```

**3. Database Connection Pooling**:
```python
# back/database/connection.py
from sqlalchemy.pool import NullPool, QueuePool

# Update engine configuration
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Increased from default 5
    max_overflow=40,       # Increased from default 10
    pool_pre_ping=True,    # Verify connections before using
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

**Frontend Optimizations**:

**1. Bundle Size Analysis**:
```bash
cd front

# Analyze bundle size
npm run build -- --stats-json
npx webpack-bundle-analyzer dist/stats.json

# Install optimization tools
npm install --save-dev @angular-devkit/build-angular
```

**2. Lazy Loading Routes**:
```typescript
// front/src/app/app.routes.ts
export const routes: Routes = [
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component')
      .then(m => m.DashboardComponent)
  },
  {
    path: 'domains',
    loadComponent: () => import('./pages/domains/domains-list.component')
      .then(m => m.DomainsListComponent)
  },
  // ... lazy load all routes
];
```

**3. Image Optimization**:
```bash
# Install image optimization
npm install --save-dev imagemin imagemin-webp

# Add to build process
```

**Deliverable**:
- 30% reduction in bundle size
- 50% improvement in API response times for cached endpoints
- Database query times < 50ms (p95)

---

### Week 4: Production Hardening

#### Day 27-28: Monitoring Setup
**Objective**: Full observability before go-live

**1. Error Tracking (Sentry)**:
```bash
# Frontend
npm install --save @sentry/angular

# Backend
pip install sentry-sdk
```

```typescript
// front/src/main.ts
import * as Sentry from "@sentry/angular";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  environment: "production",
  tracesSampleRate: 0.1,
});
```

```python
# back/api/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    environment="production",
    traces_sample_rate=0.1,
)
```

**2. Uptime Monitoring**:
- Sign up for UptimeRobot or Pingdom
- Monitor:
  - `https://smtpy.fr/` (200 OK)
  - `https://api.smtpy.fr/health` (200 OK)
  - SMTP port 1025 (if exposed)

**3. Application Metrics** (Optional but recommended):
```bash
# Install Prometheus Python client
pip install prometheus-client

# Add metrics endpoint
# back/api/metrics.py
```

**Deliverable**: Full monitoring stack operational

---

#### Day 29-30: Final Testing & Documentation
**Objective**: Verify everything works end-to-end

**Final Test Checklist**:
```markdown
## Pre-Production Checklist

### Testing
- [ ] All E2E tests passing (60+ tests)
- [ ] All frontend unit tests passing (100+ tests)
- [ ] All backend tests passing (99/99 tests, 90%+ coverage)
- [ ] Load tests show acceptable performance
- [ ] Security audit complete, no critical issues
- [ ] Manual smoke tests on staging

### Performance
- [ ] API p95 response time < 200ms
- [ ] Frontend bundle size < 500KB gzipped
- [ ] Database queries < 50ms p95
- [ ] Load test: 200 concurrent users handled

### Security
- [ ] All dependencies updated
- [ ] No critical vulnerabilities (npm audit, pip-audit)
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Secrets not in code
- [ ] CSRF protection enabled

### Monitoring
- [ ] Error tracking configured (Sentry)
- [ ] Uptime monitoring configured
- [ ] Logging aggregation working
- [ ] Metrics collection working
- [ ] Alerts configured

### Documentation
- [ ] API documentation complete
- [ ] User guides written
- [ ] Deployment guide verified
- [ ] Troubleshooting guide created
- [ ] README badges added
```

**Deliverable**: Production-ready application with comprehensive test coverage

---

## 📈 Success Metrics

### Week 1-2 Goals
- ✅ E2E tests: 60+ tests, 100% pass rate
- ✅ Frontend unit tests: 100+ tests, 80% coverage
- ✅ Backend tests: 99/99 passing, 90% coverage
- ✅ SMTP integration: 10+ tests

### Week 3-4 Goals
- ✅ Load tests: Handle 200 concurrent users
- ✅ Security: 0 critical vulnerabilities
- ✅ Performance: API < 200ms, Frontend < 500KB
- ✅ Monitoring: Full observability stack

---

## 🚀 Post-Testing: Production Launch Prep

After completing this 4-week testing sprint, you'll be ready for:

**Week 5: Production Launch**
- Final staging deployment
- Production environment setup
- DNS/SSL configuration
- Go-live

---

**Next Immediate Action**: Check E2E test results and start fixing any failures.
