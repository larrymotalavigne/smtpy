# Frontend Environment Configuration Fix

## Problem

The production frontend was making API requests to `http://localhost:8000` instead of using the correct production API URL. This caused CORS errors:

```
Access to fetch at 'http://localhost:8000/auth/register' from origin 'https://smtpy.fr'
has been blocked by CORS policy: Response to preflight request doesn't pass access control check:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause

The Angular build configuration in `angular.json` was missing the `fileReplacements` setting for the production configuration. This meant that during production builds, the build process was NOT replacing `environment.ts` with `environment.prod.ts`, causing the frontend to use development settings (localhost) even in production.

### Files Involved

1. **Environment Configuration Files:**
   - `front/src/environments/environment.ts` - Development config (uses `http://localhost:8000`)
   - `front/src/environments/environment.prod.ts` - Production config (uses `/api` relative path)

2. **Build Configuration:**
   - `front/angular.json` - Angular CLI build configuration

## Changes Made

### 1. Updated Angular Build Configuration

**File:** `front/angular.json`

Added `fileReplacements` to the production configuration:

```json
"configurations": {
  "production": {
    "outputHashing": "all",
    "fileReplacements": [
      {
        "replace": "src/environments/environment.ts",
        "with": "src/environments/environment.prod.ts"
      }
    ]
  }
}
```

This ensures that during production builds:
- `environment.ts` is replaced with `environment.prod.ts`
- The frontend uses `/api` as the API URL
- Nginx proxies `/api` requests to the backend at `http://api:8000`

### 2. Updated Node.js Version in Docker

**File:** `front/Dockerfile.prod`

Changed from Node 20 to Node 22 to meet Angular CLI requirements:

```dockerfile
FROM node:22-alpine AS builder
```

### 3. Updated Docker Compose Configuration

**File:** `docker-compose.prod.yml`

Simplified the frontend image reference to use local builds:

```yaml
frontend:
  container_name: smtpy-frontend-prod
  image: smtpy-frontend:latest
```

## Deployment

### On Production Server

1. **Pull the latest code:**
   ```bash
   git pull origin main
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy-frontend-fix.sh
   ```

This script will:
- Build a new frontend Docker image with the corrected configuration
- Stop and remove the old frontend container
- Start the new frontend container
- Display logs and status

### Manual Deployment (if needed)

If you prefer to deploy manually:

```bash
# 1. Build the new frontend image
cd front
docker build -f Dockerfile.prod -t smtpy-frontend:latest .
cd ..

# 2. Restart the frontend container
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --force-recreate frontend

# 3. Check the logs
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f frontend
```

## Verification

After deployment, verify the fix:

1. **Check the frontend is running:**
   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml ps frontend
   ```

2. **Check the logs for errors:**
   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml logs frontend
   ```

3. **Test the application:**
   - Navigate to https://smtpy.fr/auth/register
   - Try to register a new account
   - Check the browser console - there should be NO CORS errors
   - The API requests should go to `https://smtpy.fr/api/auth/register`

4. **Verify API requests in browser DevTools:**
   - Open DevTools (F12)
   - Go to Network tab
   - Try to register/login
   - You should see requests to `/api/auth/register` instead of `http://localhost:8000/auth/register`

## How the Production Setup Works

```
User Browser
    ↓
HTTPS (smtpy.fr)
    ↓
Nginx Proxy Manager (SSL termination, port 443)
    ↓
smtpy-frontend-prod (nginx:1.27-alpine, internal port 80)
    ├─ Serves Angular app (static files)
    └─ Proxies /api/* requests to backend
            ↓
    smtpy-api-prod (internal port 8000)
```

### Nginx Configuration

The frontend container's nginx is configured to:
1. Serve the Angular static files
2. Proxy requests to `/api/*` to the backend API service

The configuration is defined in:
- `front/nginx.conf` - Main nginx config
- `front/nginx-default.conf` - Default server config with API proxy rules

### Environment URLs

| Environment | Frontend URL | API URL Used by Frontend |
|------------|--------------|-------------------------|
| Development | http://localhost:4200 | http://localhost:8000 |
| Production | https://smtpy.fr | /api (proxied to backend) |

## Testing in Development

To ensure this doesn't break again:

1. **Test production build locally:**
   ```bash
   cd front
   npm run build -- --configuration production

   # Check the built files contain /api instead of localhost
   grep -r "localhost:8000" dist/sakai-ng/browser
   # Should return nothing

   grep -r "apiUrl" dist/sakai-ng/browser | head -1
   # Should show: apiUrl:"/api"
   ```

2. **Test with production Docker image:**
   ```bash
   docker build -f Dockerfile.prod -t smtpy-frontend:test .
   docker run -p 8080:80 smtpy-frontend:test
   # Visit http://localhost:8080 and check the Network tab
   ```

## Troubleshooting

### If CORS errors persist:

1. **Check the backend CORS configuration:**
   - Ensure `CORS_ORIGINS` in `.env.production` includes `https://smtpy.fr`

2. **Check Nginx Proxy Manager:**
   - Ensure the proxy host for smtpy.fr is correctly configured
   - Check that it's forwarding to the correct internal container

3. **Verify the frontend container:**
   ```bash
   # Check if the container is using the new image
   docker inspect smtpy-frontend-prod | grep Image

   # Check nginx config inside the container
   docker exec smtpy-frontend-prod cat /etc/nginx/conf.d/default.conf
   ```

4. **Check API connectivity from frontend container:**
   ```bash
   docker exec smtpy-frontend-prod wget -q -O - http://api:8000/health
   ```

## Related Files

- `front/angular.json` - Angular build configuration
- `front/src/environments/environment.ts` - Development environment
- `front/src/environments/environment.prod.ts` - Production environment
- `front/Dockerfile.prod` - Production Docker build
- `front/nginx.conf` - Nginx main configuration
- `front/nginx-default.conf` - Nginx API proxy configuration
- `docker-compose.prod.yml` - Production Docker Compose
- `deploy-frontend-fix.sh` - Deployment script

## Commit Message

```
fix(frontend): configure Angular to use production environment in builds

- Add fileReplacements to angular.json production config
- Ensure environment.prod.ts is used in production builds
- Update Node.js to v22 in Dockerfile to meet Angular CLI requirements
- Use relative /api URL in production instead of localhost:8000
- Resolves CORS errors when accessing API from production frontend

The frontend now correctly uses the /api relative path in production,
which is proxied by nginx to the backend API service. This eliminates
CORS errors that occurred when trying to access localhost:8000 from
the production domain.
```
