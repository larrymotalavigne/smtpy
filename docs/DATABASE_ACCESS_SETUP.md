# Database Access Setup - database.smtpy.fr

**Date**: 2025-12-02
**Purpose**: Configure web-based database access via HTTPS without port specification
**Status**: ✅ Ready to Deploy

---

## Overview

This setup provides secure, web-based PostgreSQL access at `https://database.smtpy.fr` using pgAdmin behind Nginx Proxy Manager. No custom ports needed - just standard HTTPS (port 443).

### Architecture

```
Internet (HTTPS/443)
   ↓
Nginx Proxy Manager (nginx.atomdev.fr)
   ↓ SSL Termination
Docker Network (smtpy-network)
   ↓
pgAdmin Container (port 80) ←→ PostgreSQL Database
```

### Benefits

- ✅ **No port specification** - Access via standard HTTPS (443)
- ✅ **Web-based interface** - No local database client needed
- ✅ **SSL/TLS encryption** - Handled by NPM with Let's Encrypt
- ✅ **Double authentication** - pgAdmin login + PostgreSQL credentials
- ✅ **No direct database exposure** - Database port stays internal
- ✅ **Full SQL features** - Query editor, table browser, import/export
- ✅ **Multi-user support** - Create multiple pgAdmin users

---

## Setup Instructions

### Step 1: Update Environment Variables

Edit your `.env.production` file and add pgAdmin credentials:

```bash
# Edit environment file
nano /srv/smtpy/.env.production
```

Add or update these variables:

```bash
# =============================================================================
# PGADMIN CONFIGURATION (Web-based Database Management)
# =============================================================================

# pgAdmin login email (use a real email for your support team)
PGADMIN_EMAIL=support@smtpy.fr

# pgAdmin password (generate a strong password)
# Generate with: openssl rand -base64 32
PGADMIN_PASSWORD=your_strong_pgadmin_password_here
```

**Generate a strong password**:
```bash
openssl rand -base64 32
```

### Step 2: Deploy the pgAdmin Container

The pgAdmin service is already configured in `docker-compose.prod.yml`. Deploy it:

```bash
cd /srv/smtpy

# Pull the pgAdmin image
docker compose -f docker-compose.prod.yml pull pgadmin

# Start pgAdmin (and other services if needed)
docker compose -f docker-compose.prod.yml up -d pgadmin

# Verify it's running
docker ps | grep pgadmin
# Should show: smtpy-pgadmin-prod

# Check health
docker logs smtpy-pgadmin-prod
```

### Step 3: Connect NPM to SMTPy Network

If not already done, connect Nginx Proxy Manager to the SMTPy Docker network:

```bash
# Find your NPM container name
docker ps | grep nginx-proxy-manager

# Connect NPM to SMTPy network (replace <npm-container-name>)
docker network connect smtpy_smtpy-network <npm-container-name>

# Verify connection
docker network inspect smtpy_smtpy-network | grep -A 5 npm
```

### Step 4: Configure DNS

Point `database.smtpy.fr` to your server's public IP:

```
# A Record
database.smtpy.fr → <your-server-ip>
```

Verify DNS resolution:
```bash
nslookup database.smtpy.fr
# Should return your server IP
```

### Step 5: Create NPM Proxy Host

1. **Login to Nginx Proxy Manager** UI (usually `http://<server-ip>:81`)

2. **Navigate to**: Hosts → Proxy Hosts → **Add Proxy Host**

3. **Configure the Details Tab**:
   ```
   Domain Names:     database.smtpy.fr
   Scheme:           http (internal communication is unencrypted)
   Forward Hostname: smtpy-pgadmin-prod
   Forward Port:     80
   Cache Assets:     ✅ Enabled
   Block Common Exploits: ✅ Enabled
   Websockets Support: ❌ Disabled (not needed for pgAdmin)
   ```

4. **Configure the SSL Tab**:
   ```
   SSL Certificate:  Request a New SSL Certificate
   Force SSL:        ✅ Enabled
   HTTP/2 Support:   ✅ Enabled
   HSTS Enabled:     ✅ Enabled
   HSTS Subdomains:  ❌ Disabled (unless you have subdomains)
   Email:            your-email@domain.com (for Let's Encrypt)
   Agree to Terms:   ✅ Enabled
   ```

5. **Configure the Advanced Tab** (optional but recommended):
   ```nginx
   # Client upload limits for query results and imports
   client_max_body_size 100M;
   client_body_buffer_size 128k;

   # Security headers
   add_header X-Frame-Options "SAMEORIGIN" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header Referrer-Policy "no-referrer-when-downgrade" always;

   # Timeouts for long-running queries
   proxy_read_timeout 600s;
   proxy_connect_timeout 600s;
   proxy_send_timeout 600s;
   ```

6. **Save** the proxy host configuration

### Step 6: Test Access

1. **Test DNS and HTTP connectivity**:
   ```bash
   # Test from NPM container
   docker exec <npm-container-name> curl -f http://smtpy-pgadmin-prod:80/misc/ping

   # Should return: {"status": "ok"}
   ```

2. **Test external HTTPS access**:
   ```bash
   curl -I https://database.smtpy.fr
   # Should return: 200 OK
   ```

3. **Access via browser**:
   - Navigate to: `https://database.smtpy.fr`
   - You should see the pgAdmin login page

---

## First-Time pgAdmin Configuration

### Login to pgAdmin

1. Open browser and go to: `https://database.smtpy.fr`

2. **Login with pgAdmin credentials**:
   - Email: `support@smtpy.fr` (or whatever you set in PGADMIN_EMAIL)
   - Password: (the password you set in PGADMIN_PASSWORD)

### Add PostgreSQL Server Connection

After logging in, you need to add the SMTPy database:

1. **Click**: Servers (in left sidebar) → Right-click → **Create** → **Server**

2. **General Tab**:
   ```
   Name: SMTPy Production Database
   ```

3. **Connection Tab**:
   ```
   Host name/address:  db  (or smtpy-db-prod)
   Port:               5432
   Maintenance database: smtpy
   Username:           postgres
   Password:           (your POSTGRES_PASSWORD from .env.production)
   Save password:      ✅ Yes
   ```

4. **SSL Tab** (optional):
   ```
   SSL mode: Prefer
   ```

5. **Advanced Tab** (optional):
   ```
   DB restriction: smtpy
   ```

6. **Click**: **Save**

You should now see the database in the left sidebar and can browse tables, run queries, etc.

---

## Usage Guide

### Basic Operations

#### Browse Tables
1. Expand: **Servers** → **SMTPy Production Database** → **Databases** → **smtpy** → **Schemas** → **public** → **Tables**
2. Right-click any table → **View/Edit Data** → **All Rows**

#### Run SQL Queries
1. Right-click **smtpy** database → **Query Tool**
2. Write your SQL query
3. Press **F5** or click **Execute** button

Example queries:
```sql
-- View all users
SELECT id, email, created_at FROM users LIMIT 10;

-- Count messages
SELECT COUNT(*) FROM messages;

-- Check domain configuration
SELECT domain, is_verified, created_at FROM domains;

-- View recent aliases
SELECT alias, destination, created_at
FROM aliases
ORDER BY created_at DESC
LIMIT 10;
```

#### Export Data
1. Right-click table → **Import/Export**
2. Choose format (CSV, Excel, JSON)
3. Configure options
4. **OK** to download

#### Import Data
1. Right-click table → **Import/Export**
2. Toggle to **Import**
3. Upload file
4. Map columns
5. **OK** to import

### Creating Read-Only Support Users (Recommended)

For security, create a read-only PostgreSQL user for support access:

```sql
-- Connect as postgres user, then run:

-- Create read-only user
CREATE USER support_readonly WITH PASSWORD 'strong_password_here';

-- Grant connection
GRANT CONNECT ON DATABASE smtpy TO support_readonly;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO support_readonly;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO support_readonly;

-- Grant SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO support_readonly;
```

Then add this user as a separate connection in pgAdmin for support staff.

### Creating Multiple pgAdmin Users

pgAdmin supports multiple users with different permissions:

1. **Click**: Object → **User Management** (top menu)
2. **Add User**:
   - Email: `support-user@smtpy.fr`
   - Password: (generate strong password)
   - Role: User (limited) or Administrator (full access)
3. **Save**

Each user can have their own saved database connections and queries.

---

## Security Best Practices

### 1. Strong Passwords

Always use strong passwords for:
- ✅ pgAdmin login (`PGADMIN_PASSWORD`)
- ✅ PostgreSQL `postgres` user (`POSTGRES_PASSWORD`)
- ✅ Read-only support users

Generate with:
```bash
openssl rand -base64 32
```

### 2. IP Whitelisting (Optional but Recommended)

Restrict access to `database.smtpy.fr` to known IPs:

**In NPM → Access Lists**:
1. Create new Access List
2. Name: "Support Team IPs"
3. Add allowed IP addresses/ranges
4. Apply to `database.smtpy.fr` proxy host

**Or via firewall**:
```bash
# Allow specific IPs to access HTTPS
sudo iptables -A INPUT -p tcp --dport 443 -s <support-ip-1> -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -s <support-ip-2> -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j DROP

# Save rules
sudo netfilter-persistent save
```

### 3. Enable Master Password

pgAdmin supports a master password for additional security:

1. **File** → **Preferences** → **Security**
2. Enable **Master Password**
3. Set a strong master password
4. This encrypts saved database passwords

### 4. Regular Audit

Monitor who's accessing pgAdmin:

```bash
# View pgAdmin logs
docker logs smtpy-pgadmin-prod -f

# Filter for login attempts
docker logs smtpy-pgadmin-prod 2>&1 | grep -i login

# View NPM access logs for database.smtpy.fr
docker logs <npm-container-name> -f | grep database.smtpy.fr
```

### 5. Use Read-Only Users

For regular support tasks, use the read-only user instead of `postgres`:
- Less risk of accidental data modification
- Better audit trail
- Follows principle of least privilege

### 6. Backup Before Modifications

Always backup before running UPDATE/DELETE queries:

```sql
-- Backup a table
CREATE TABLE users_backup AS SELECT * FROM users;

-- Or export via pgAdmin before modifications
```

---

## Troubleshooting

### Issue: "502 Bad Gateway" when accessing database.smtpy.fr

**Check 1**: Is pgAdmin running?
```bash
docker ps | grep pgadmin
docker logs smtpy-pgadmin-prod
```

**Check 2**: Is NPM connected to the network?
```bash
docker network inspect smtpy_smtpy-network | grep npm
```

**Check 3**: Can NPM reach pgAdmin?
```bash
docker exec <npm-container-name> ping smtpy-pgadmin-prod
docker exec <npm-container-name> curl http://smtpy-pgadmin-prod:80/misc/ping
```

### Issue: "Cannot connect to database server" in pgAdmin

**Check 1**: Is PostgreSQL running?
```bash
docker ps | grep db
docker logs smtpy-db-prod
```

**Check 2**: Are credentials correct?
```bash
# Verify from pgAdmin container
docker exec smtpy-pgadmin-prod ping db
```

**Check 3**: Test connection manually
```bash
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "SELECT 1;"
```

### Issue: SSL Certificate Failed in NPM

**Cause**: DNS not propagated or port 80/443 blocked

**Fix**:
```bash
# Verify DNS
nslookup database.smtpy.fr

# Test port 80 accessibility
curl -I http://database.smtpy.fr

# Check firewall
sudo ufw status | grep -E "80|443"
```

### Issue: "Connection Refused" from pgAdmin to PostgreSQL

**Cause**: pgAdmin and DB not on same network

**Fix**:
```bash
# Verify both are on smtpy-network
docker network inspect smtpy_smtpy-network
```

---

## Comparison: Web-Based vs Other Methods

| Method | Accessibility | Security | Setup Complexity | Best For |
|--------|--------------|----------|------------------|----------|
| **pgAdmin Web** | ✅ Browser, any device | ⭐⭐⭐⭐ High | Easy | Support teams, multiple users |
| **SSH Tunnel** | ❌ Requires SSH + client | ⭐⭐⭐⭐⭐ Very High | Medium | Power users, CLI |
| **Direct DB Exposure** | ✅ Any DB client | ⭐⭐ Low | Easy | ❌ Not recommended |
| **VPN Access** | ❌ VPN required | ⭐⭐⭐⭐⭐ Very High | Complex | Enterprise |

---

## Alternative Web Tools

If you prefer lighter alternatives to pgAdmin:

### Adminer (Ultra-lightweight)

**docker-compose.prod.yml**:
```yaml
  adminer:
    container_name: smtpy-adminer-prod
    image: adminer:latest
    environment:
      ADMINER_DEFAULT_SERVER: db
    networks:
      - smtpy-network
    restart: unless-stopped
```

**NPM**: Forward `database.smtpy.fr` to `smtpy-adminer-prod:8080`

**Pros**: Tiny (1 file), fast, simple UI
**Cons**: Fewer features than pgAdmin

### pgweb (Modern, Minimal)

**docker-compose.prod.yml**:
```yaml
  pgweb:
    container_name: smtpy-pgweb-prod
    image: sosedoff/pgweb:latest
    environment:
      DATABASE_URL: postgres://postgres:${POSTGRES_PASSWORD}@db:5432/smtpy?sslmode=disable
    networks:
      - smtpy-network
    restart: unless-stopped
```

**NPM**: Forward `database.smtpy.fr` to `smtpy-pgweb-prod:8081`

**Pros**: Modern UI, fast, SSH support
**Cons**: Limited compared to pgAdmin

---

## Maintenance

### Update pgAdmin

```bash
# Pull latest image
docker compose -f docker-compose.prod.yml pull pgadmin

# Recreate container
docker compose -f docker-compose.prod.yml up -d pgadmin

# Verify
docker logs smtpy-pgadmin-prod
```

### Backup pgAdmin Configuration

pgAdmin stores configurations in its volume:

```bash
# Backup pgAdmin data
docker run --rm \
  -v smtpy_pgadmin_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/pgadmin-backup-$(date +%Y%m%d).tar.gz /data

# List backups
ls -lh pgadmin-backup-*.tar.gz
```

### Restore pgAdmin Configuration

```bash
# Restore from backup
docker run --rm \
  -v smtpy_pgadmin_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/pgadmin-backup-20251202.tar.gz -C /
```

---

## Resource Usage

pgAdmin container resource limits:
- **CPU**: 0.5 cores max, 0.25 reserved
- **Memory**: 512MB max, 256MB reserved
- **Disk**: ~100MB image + data volume

Typical usage:
- Idle: ~50MB RAM, minimal CPU
- Active queries: ~200MB RAM, 10-30% CPU
- Export/import: ~400MB RAM, 50%+ CPU

---

## Quick Reference Commands

```bash
# View pgAdmin logs
docker logs smtpy-pgadmin-prod -f

# Restart pgAdmin
docker restart smtpy-pgadmin-prod

# Check pgAdmin health
docker exec smtpy-pgadmin-prod wget -O - http://localhost:80/misc/ping

# Access pgAdmin shell (for troubleshooting)
docker exec -it smtpy-pgadmin-prod /bin/sh

# View pgAdmin environment
docker exec smtpy-pgadmin-prod env | grep PGADMIN

# Check pgAdmin volume
docker volume inspect smtpy_pgadmin_data
```

---

## Related Documentation

- [NGINX_PROXY_MANAGER_SETUP.md](./NGINX_PROXY_MANAGER_SETUP.md) - NPM configuration
- [DATABASE_MANAGEMENT.md](./DATABASE_MANAGEMENT.md) - Database backups and maintenance
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - General deployment instructions

---

**Last Updated**: 2025-12-02
**Status**: ✅ Ready for Production
**Tested With**: pgAdmin 4 (latest), PostgreSQL 18-alpine
