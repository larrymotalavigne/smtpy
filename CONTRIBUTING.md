# Contributing to SMTPy

Thank you for your interest in contributing to SMTPy! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+ (LTS recommended)
- Docker and Docker Compose
- Git
- uv (Python package manager)

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/larrymotalavigne/smtpy.git
   cd smtpy
   ```

2. **Backend Setup**
   ```bash
   cd back
   uv sync
   cp .env.example .env
   # Edit .env with your local configuration
   ```

3. **Frontend Setup**
   ```bash
   cd front
   npm install
   ```

4. **Start Development Environment**
   ```bash
   # From project root
   make dev  # Starts all services with Docker Compose
   ```

5. **Run Tests**
   ```bash
   # Backend tests
   cd back
   uv run pytest

   # Frontend tests
   cd front
   npm test

   # E2E tests
   npm run test:e2e
   ```

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical production fixes

### Workflow

1. Create a new branch from `main` or `develop`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Write/update tests for your changes

4. Ensure all tests pass
   ```bash
   make test
   ```

5. Commit your changes following commit guidelines

6. Push your branch and create a pull request

## Coding Standards

### Python (Backend)

- **Style Guide**: PEP 8
- **Line Length**: 100 characters (configured in ruff and black)
- **Type Hints**: Required for all functions
- **Formatting**: Use `black` and `ruff`
- **Linting**: Use `mypy` for type checking

**Run formatters and linters**:
```bash
cd back
uv run black .
uv run ruff check --fix .
uv run mypy .
```

**Architecture Pattern** (3-layer):
```python
# views/*.py - FastAPI routes, request/response handling
# controllers/*.py - Business logic (pure functions)
# database/*.py - Database queries (SQLAlchemy async)
```

**Example**:
```python
# Good: Type hints, descriptive names, docstrings
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Retrieve a user by their email address.

    Args:
        db: Async database session
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### TypeScript/Angular (Frontend)

- **Style Guide**: Angular style guide
- **Line Length**: 100 characters
- **Formatting**: Use Prettier
- **Linting**: Use ESLint

**Run formatters and linters**:
```bash
cd front
npm run lint
npm run format
```

**Component Structure**:
```typescript
// Use standalone components (no NgModules)
@Component({
  selector: 'app-example',
  standalone: true,
  imports: [CommonModule, FormsModule, /* ... */],
  templateUrl: './example.component.html',
  styleUrls: ['./example.component.scss']
})
export class ExampleComponent implements OnInit {
  // Properties first
  data: DataType[] = [];
  loading = false;
  error: string | null = null;

  // Constructor with dependency injection
  constructor(private dataService: DataService) {}

  // Lifecycle hooks
  ngOnInit(): void {
    this.loadData();
  }

  // Methods
  loadData(): void {
    this.loading = true;
    this.dataService.getData().subscribe({
      next: (data) => {
        this.data = data;
        this.loading = false;
      },
      error: (error) => {
        this.error = 'Failed to load data';
        this.loading = false;
      }
    });
  }
}
```

## Testing Requirements

### Backend Tests

- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test API endpoints with database
- **Coverage Target**: 90%+

**Test Structure**:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestUserAPI:
    async def test_create_user_success(self, client: AsyncClient):
        """Test successful user creation"""
        response = await client.post("/users", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"

    async def test_create_user_duplicate_email(self, client: AsyncClient):
        """Test user creation with duplicate email fails"""
        # Test implementation
        pass
```

### Frontend Tests

- **Unit Tests**: Test components, services, pipes
- **E2E Tests**: Test complete user flows
- **Coverage Target**: 80%+

**Component Test Example**:
```typescript
describe('ExampleComponent', () => {
  let component: ExampleComponent;
  let fixture: ComponentFixture<ExampleComponent>;
  let mockService: jasmine.SpyObj<DataService>;

  beforeEach(async () => {
    mockService = jasmine.createSpyObj('DataService', ['getData']);

    await TestBed.configureTestingModule({
      imports: [ExampleComponent],
      providers: [
        { provide: DataService, useValue: mockService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ExampleComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load data on init', () => {
    const mockData = [{ id: 1, name: 'Test' }];
    mockService.getData.and.returnValue(of(mockData));

    fixture.detectChanges();

    expect(component.data).toEqual(mockData);
    expect(mockService.getData).toHaveBeenCalled();
  });
});
```

### E2E Tests (Playwright)

```typescript
test('should complete user registration flow', async ({ page }) => {
  await page.goto('/register');

  await page.fill('[name="email"]', 'newuser@example.com');
  await page.fill('[name="password"]', 'SecurePass123!');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system or dependencies changes
- `ci`: CI/CD changes
- `chore`: Other changes that don't modify src or test files

### Examples

```bash
feat(auth): add password reset functionality

Implement password reset flow with email verification.
Users can now request a password reset link via email.

Closes #123

---

fix(billing): correct Stripe webhook signature verification

The webhook signature was not being verified correctly,
causing legitimate webhooks to be rejected.

---

docs(deployment): add production SSL setup guide

Added comprehensive guide for setting up Let's Encrypt
SSL certificates in production environment.
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass (`make test`)
2. ✅ Code is formatted (`make format`)
3. ✅ No linting errors (`make lint`)
4. ✅ Documentation is updated (if needed)
5. ✅ CHANGELOG.md is updated
6. ✅ Commit messages follow guidelines

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] CHANGELOG.md updated

## Screenshots (if applicable)

## Related Issues
Closes #(issue number)
```

### Review Process

1. At least one approval required from maintainers
2. All CI checks must pass
3. No unresolved review comments
4. Branch must be up to date with target branch

## Project Structure

```
smtpy/
├── back/                       # Backend (Python/FastAPI)
│   ├── api/                    # API application
│   │   ├── controllers/        # Business logic
│   │   ├── database/           # Database queries
│   │   ├── views/              # API endpoints
│   │   ├── schemas/            # Pydantic models
│   │   └── services/           # External services
│   ├── smtp/                   # SMTP server
│   │   ├── smtp_server/        # Server implementation
│   │   └── forwarding/         # Email forwarding
│   ├── tests/                  # Backend tests
│   └── migrations/             # Alembic migrations
├── front/                      # Frontend (Angular)
│   ├── src/app/
│   │   ├── core/               # Core services, guards
│   │   ├── features/           # Feature components
│   │   └── shared/             # Shared components
│   └── e2e/                    # Playwright E2E tests
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
└── docker-compose*.yml         # Docker configurations
```

## Key Design Principles

1. **Separation of Concerns**: Backend uses 3-layer architecture
2. **Type Safety**: TypeScript strict mode, Python type hints
3. **Async/Await**: All I/O operations are async
4. **Error Handling**: Comprehensive error handling at all layers
5. **Security First**: Input validation, authentication, rate limiting
6. **Testability**: Write testable code with dependency injection

## Getting Help

- **Documentation**: Check `/docs` folder for detailed guides
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: [Add contact email]

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project website (when available)

---

Thank you for contributing to SMTPy! 🚀
