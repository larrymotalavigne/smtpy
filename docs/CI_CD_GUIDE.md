# CI/CD Pipeline Documentation

**Last Updated**: October 26, 2025
**Pipeline Version**: 2.0 (Production-ready)

## Overview

The SMTPy CI/CD pipeline automates testing, building, and deployment of the application using GitHub Actions. The pipeline is optimized for production deployment with multi-stage Docker builds, security scanning, and comprehensive health checks.

## Pipeline Architecture

### Workflow File

`.github/workflows/ci-cd.yml`

### Trigger Events

The pipeline runs on:
- **Push to main**: Full pipeline including deployment
- **Push to develop**: Build and test only (no deployment)
- **Pull Requests to main**: Build and test only
- **Version tags** (`v*`): Build with semantic versioning

## Pipeline Stages

### 1. Test Stage

**Job**: `test`
**Duration**: ~3-5 minutes

**Steps**:
1. Checkout code
2. Set up Python 3.13
3. Install dependencies via Makefile
4. Run test suite with coverage
5. Upload test results as artifacts

**Artifacts**:
- HTML coverage report (`htmlcov/`)
- Coverage data (`.coverage`)

**Commands**:
```bash
make install  # Install dependencies using uv
make test     # Run pytest with coverage
```

**Coverage Requirements**:
- Current: 59% (baseline)
- Target: 70%+ (in progress)

### 2. Lint Stage

**Job**: `lint`
**Duration**: ~1-2 minutes
**Runs in parallel with**: Test stage

**Steps**:
1. Checkout code
2. Set up Python 3.13
3. Install dependencies
4. Run linter (Ruff)

**Commands**:
```bash
make lint  # Run ruff check
```

**Note**: Currently set to non-blocking (`|| true`) to avoid failing builds during transition period.

### 3. Security Scan Stage

**Job**: `security-scan`
**Duration**: ~2-3 minutes
**Runs in parallel with**: Test and Lint stages

**Tools**:
- **Trivy**: Vulnerability scanner for filesystem and dependencies

**Steps**:
1. Checkout code
2. Run Trivy scanner
3. Upload results to GitHub Security tab

**Output**:
- SARIF format results
- Visible in GitHub Security > Code scanning alerts

### 4. Build and Push Stage

**Job**: `build-and-push`
**Duration**: ~10-15 minutes
**Depends on**: Test and Lint stages
**Runs**: After tests and linting pass

**Strategy**: Matrix build for 3 services
- API (back/api/Dockerfile.prod)
- SMTP (back/smtp/Dockerfile.prod)
- Frontend (front/Dockerfile.prod)

**Features**:
- **Multi-stage builds**: Optimized production images
- **Docker Buildx**: Advanced build capabilities
- **Layer caching**: GitHub Actions cache for faster builds
- **Metadata extraction**: Automatic tagging with semantic versioning

**Image Tags Generated**:
- `latest` (on main branch only)
- `<branch-name>` (for branch pushes)
- `<version>` (for semantic version tags like v1.0.0)
- `<major>.<minor>` (for version tags)
- `<branch>-<sha>` (unique identifier for each commit)

**Registry**: GitHub Container Registry (ghcr.io)

**Example Tags**:
```
ghcr.io/larrymotalavigne/smtpy-api:latest
ghcr.io/larrymotalavigne/smtpy-api:main
ghcr.io/larrymotalavigne/smtpy-api:v1.0.0
ghcr.io/larrymotalavigne/smtpy-api:1.0
ghcr.io/larrymotalavigne/smtpy-api:main-abc1234
```

### 5. Deploy Stage

**Job**: `deploy`
**Duration**: ~5-10 minutes
**Depends on**: Build and Push stage
**Runs**: Only on main branch pushes
**Environment**: production (https://smtpy.fr)

**Deployment Strategy**: Rolling update for zero downtime

**Steps**:
1. Copy production files to server:
   - `docker-compose.prod.yml`
   - `.env.production.template`

2. Login to GitHub Container Registry

3. Pull latest images

4. Rolling deployment:
   - Update database and Redis (stable services)
   - Update API with rolling restart (scale 1→2 for HA)
   - Update SMTP server
   - Update frontend

5. Clean up unused images

6. Display running containers

**Zero-Downtime Deployment**:
```bash
# Scale API to 1 replica
docker compose up -d --no-deps --scale api=1 api

# Wait 10 seconds for health checks
sleep 10

# Scale back to 2 replicas (new version)
docker compose up -d --no-deps --scale api=2 api
```

**Benefits**:
- Old version serves traffic during update
- New version health-checked before taking traffic
- No service interruption

### 6. Health Check Stage

**Job**: `health-check`
**Duration**: ~2-3 minutes
**Depends on**: Deploy stage
**Runs**: Only on main branch pushes

**Two-Level Verification**:

1. **Internal Verification** (scripts/verify-deployment.sh):
   - Prerequisites check
   - Environment validation
   - Docker Compose config validation
   - Service status
   - Resource usage
   - Log analysis
   - Database operations
   - Security checks

2. **External Health Checks**:
   - API health endpoint (https://smtpy.fr/health)
   - SMTP server socket connection
   - Frontend accessibility
   - Database readiness
   - Redis connectivity

**Exit Behavior**:
- **Success**: Deployment complete, services healthy
- **Failure**: Rollback recommended, alerts triggered

## Pipeline Configuration

### Environment Variables

**Global Variables** (defined in workflow):
```yaml
REGISTRY: ghcr.io
OWNER: larrymotalavigne
```

### GitHub Secrets

Required secrets for the pipeline:

| Secret Name | Purpose | Used In |
|-------------|---------|---------|
| `GITHUB_TOKEN` | GitHub Container Registry auth | Build & Push |
| `UNRAID_SSH_HOST` | Production server hostname | Deploy & Health Check |
| `UNRAID_SSH_USER` | SSH username | Deploy & Health Check |
| `UNRAID_SSH_KEY` | SSH private key | Deploy & Health Check |
| `REGISTRY_USERNAME` | GHCR username | Deploy |
| `REGISTRY_PASSWORD` | GHCR password/token | Deploy |

### Setting Up Secrets

1. Go to repository Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Add each secret listed above

**SSH Key Setup**:
```bash
# Generate SSH key pair (if needed)
ssh-keygen -t ed25519 -C "github-actions"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server

# Copy private key content to GitHub secret UNRAID_SSH_KEY
cat ~/.ssh/id_ed25519
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Trigger Event                           │
│  (Push to main/develop, PR to main, Version tag)           │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────┬──────────┬──────────────┐
             │      │          │              │
             ▼      ▼          ▼              ▼
         ┌─────┐ ┌────┐  ┌──────────┐   (Parallel)
         │Test │ │Lint│  │Security  │
         │     │ │    │  │Scan      │
         └──┬──┘ └──┬─┘  └────┬─────┘
            │       │         │
            └───┬───┴─────────┘
                │
                ▼
         ┌─────────────────┐
         │ Build & Push    │
         │ (Matrix: 3)     │
         │ - API           │
         │ - SMTP          │
         │ - Frontend      │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Deploy          │
         │ (main only)     │
         │ Rolling Update  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Health Check    │
         │ (comprehensive) │
         └─────────────────┘
```

## Usage Examples

### Standard Development Workflow

1. **Create feature branch**:
```bash
git checkout -b feature/new-feature
# Make changes
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

2. **Create Pull Request**:
- Pipeline runs: Test + Lint + Security Scan + Build
- No deployment
- Review test results in PR

3. **Merge to main**:
```bash
git checkout main
git merge feature/new-feature
git push origin main
```

4. **Pipeline runs full deployment**:
- All stages including Deploy and Health Check
- Automatic deployment to production
- Health checks verify deployment

### Release Workflow

1. **Create release tag**:
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. **Pipeline builds with semantic versioning**:
- Images tagged as `v1.0.0`, `1.0`, `latest`
- No deployment (tag push doesn't deploy)
- Ready for manual production deployment

3. **Deploy specific version**:
```bash
# On production server
export TAG=v1.0.0
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Rollback Procedure

If deployment fails or issues are detected:

1. **Identify last working version**:
```bash
# Check GHCR for previous tags
# Example: v1.0.0 was last working version
```

2. **Deploy previous version**:
```bash
# On production server
export TAG=v1.0.0
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

3. **Verify rollback**:
```bash
./scripts/verify-deployment.sh
```

## Monitoring Pipeline

### GitHub Actions UI

View pipeline runs:
1. Go to repository > Actions tab
2. Click on specific workflow run
3. View each job's logs

### Artifacts

Download test artifacts:
1. Go to workflow run
2. Scroll to "Artifacts" section
3. Download test results and coverage reports

### Security Alerts

View security scan results:
1. Go to repository > Security tab
2. Click "Code scanning alerts"
3. Review Trivy findings

## Performance Optimization

### Build Cache

Pipeline uses GitHub Actions cache for Docker layers:
- **cache-from**: `type=gha` (read from cache)
- **cache-to**: `type=gha,mode=max` (write to cache)

**Benefits**:
- First build: ~15 minutes
- Subsequent builds: ~5-8 minutes (if dependencies unchanged)

### Parallel Execution

Jobs that can run in parallel:
- Test
- Lint
- Security Scan

**Total time savings**: ~5-10 minutes per pipeline run

### Matrix Builds

Build all 3 services in parallel:
- Reduces total build time by 3x
- Independent service builds

## Troubleshooting

### Build Failures

**Symptom**: Build stage fails

**Common Causes**:
1. Docker build context issues
2. Missing dependencies
3. Syntax errors in Dockerfile

**Solution**:
```bash
# Test build locally
docker build -f back/api/Dockerfile.prod -t test-api .

# Check build logs
docker build --progress=plain -f back/api/Dockerfile.prod .
```

### Deployment Failures

**Symptom**: Deploy stage fails

**Common Causes**:
1. SSH connection issues
2. Docker Compose errors
3. Environment variables not set

**Solution**:
```bash
# Test SSH connection
ssh -p 2345 user@host

# Validate docker-compose.prod.yml
docker compose -f docker-compose.prod.yml config

# Check environment variables on server
ssh user@host "cat /srv/smtpy/.env.production"
```

### Health Check Failures

**Symptom**: Health check stage fails

**Common Causes**:
1. Services not fully started
2. Configuration errors
3. Database migration issues

**Solution**:
```bash
# SSH to server and check logs
docker compose -f docker-compose.prod.yml logs api

# Run verification manually
./scripts/verify-deployment.sh --verbose

# Check individual service health
docker compose -f docker-compose.prod.yml ps
```

### Image Push Failures

**Symptom**: Cannot push to GHCR

**Common Causes**:
1. Authentication issues
2. Package permissions
3. Registry rate limits

**Solution**:
1. Verify GITHUB_TOKEN has package write permissions
2. Check repository Settings > Actions > General > Workflow permissions
3. Ensure "Read and write permissions" is selected

## Best Practices

### 1. Semantic Versioning

Use semantic versioning for releases:
```bash
# Major version (breaking changes)
git tag v2.0.0

# Minor version (new features)
git tag v1.1.0

# Patch version (bug fixes)
git tag v1.0.1
```

### 2. Feature Branches

Always develop in feature branches:
```bash
git checkout -b feature/feature-name
git checkout -b fix/bug-description
git checkout -b refactor/component-name
```

### 3. Pull Request Reviews

- Require PR reviews before merging to main
- Use GitHub branch protection rules
- Review test results in PR

### 4. Environment Management

- Never commit `.env.production` to git
- Use GitHub secrets for sensitive data
- Validate environment on server before deployment

### 5. Monitoring

- Check pipeline runs regularly
- Review security scan results
- Monitor deployment health checks
- Set up notifications for failures

## Future Enhancements

### Planned Improvements

1. **Test Coverage Enforcement**
   - Fail builds if coverage drops below threshold
   - Upload coverage to Codecov

2. **Automated Changelog**
   - Generate changelog from commits
   - Use conventional commits

3. **Staging Environment**
   - Deploy to staging before production
   - Require manual approval for production

4. **Performance Testing**
   - Add load testing stage
   - Benchmark API performance

5. **Notification System**
   - Slack/Discord notifications
   - Email alerts for failures

6. **Multi-Architecture Builds**
   - Build for ARM64 and AMD64
   - Support multiple platforms

## References

### Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Docker Metadata Action](https://github.com/docker/metadata-action)

### Related Files

- `.github/workflows/ci-cd.yml` - Pipeline configuration
- `docker-compose.prod.yml` - Production deployment config
- `scripts/verify-deployment.sh` - Health check script
- `docs/DEPLOYMENT_GUIDE.md` - Deployment documentation

## Support

For pipeline issues:
1. Check GitHub Actions logs
2. Review this documentation
3. Check deployment guide for server issues
4. Create GitHub issue if problem persists

---

**Pipeline Status**: ✅ Production-ready
**Last Review**: October 26, 2025
**Next Review**: After implementing staging environment
