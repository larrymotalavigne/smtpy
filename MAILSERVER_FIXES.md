# Mailserver Configuration Fixes

## Overview

This document describes the fixes implemented to resolve issues with fresh mailserver instances.

## Issues Fixed

### 1. Postscreen PREGREET Violations

**Problem:**
Health checks were being blocked by Postfix's postscreen with PREGREET violations:
```
PREGREET 18 after 0 from [127.0.0.1]:55496: EHLO healthcheck\r\n
```

**Root Cause:**
Postscreen is an anti-spam feature that blocks clients sending commands before receiving the SMTP banner. Even though the health check script properly waits for the banner, postscreen was enforcing this check on localhost connections.

**Solution:**
Created `config/mailserver/postscreen_access.cidr` to whitelist localhost and Docker networks from postscreen checks:
- Whitelists `127.0.0.0/8` (localhost)
- Whitelists `::1` (IPv6 localhost)
- Whitelists Docker bridge networks (`172.16.0.0/12`, `10.0.0.0/8`)

Updated `config/mailserver/postfix-main.cf` to use the whitelist:
```
postscreen_access_list = permit_mynetworks,
                        cidr:/tmp/docker-mailserver/postscreen_access.cidr
```

### 2. Missing Postfix Database Files

**Problem:**
Errors on startup:
```
error: open database /tmp/docker-mailserver/postfix-virtual.cf.db: No such file or directory
```

**Root Cause:**
Postfix requires `.db` files to be generated from configuration files using the `postmap` command. These were not being generated on fresh instances.

**Solution:**
Created `scripts/setup-mailserver.sh` that:
- Waits for Postfix to start
- Generates database files using `postmap`:
  - `postfix-virtual.cf.db` from `postfix-virtual.cf`
  - `postfix-transport.db` from `postfix-transport`
- Reloads Postfix configuration
- Waits for Rspamd to be ready

The setup script is automatically run by `scripts/deploy-mailserver.sh` after container startup.

### 3. Milter Service Connection Refused

**Problem:**
Warnings on startup:
```
warning: connect to Milter service inet:localhost:11332: Connection refused
```

**Root Cause:**
Rspamd (which provides the milter service on port 11332) takes time to start. Postfix was attempting to connect before Rspamd was ready, causing connection failures.

**Solution:**
Updated `config/mailserver/postfix-main.cf` with milter configuration that allows mail to flow even when Rspamd is unavailable:
```
smtpd_milters = inet:localhost:11332
non_smtpd_milters = $smtpd_milters
milter_default_action = accept
milter_protocol = 6
```

The `milter_default_action = accept` setting means:
- Mail is accepted even if the milter service is unavailable
- Prevents mail rejection during Rspamd startup
- Allows the system to gracefully handle temporary milter outages

Additionally, the setup script waits for Rspamd to be ready before completing.

## Files Modified

### New Files
1. **config/mailserver/postscreen_access.cidr** - Postscreen whitelist
2. **scripts/setup-mailserver.sh** - Mailserver initialization script

### Modified Files
1. **config/mailserver/postfix-main.cf** - Added postscreen and milter configuration
2. **docker-compose.prod.yml** - Added volume mounts for new files
3. **scripts/deploy-mailserver.sh** - Added automatic setup script execution

## Deployment

The fixes are automatically applied when deploying the mailserver:

```bash
sudo ./scripts/deploy-mailserver.sh
```

The deployment script will:
1. Start the mailserver container
2. Wait for it to become healthy
3. Automatically run the setup script
4. Generate required database files
5. Configure Postfix properly

## Manual Setup

If you need to manually run the setup script:

```bash
docker exec mailserver bash /usr/local/bin/setup-mailserver.sh
```

## Verification

After deployment, verify the fixes:

1. **Check health status:**
   ```bash
   docker exec mailserver bash /usr/local/bin/healthcheck.sh
   ```

2. **Check for PREGREET violations:**
   ```bash
   docker logs mailserver | grep PREGREET
   ```
   Should return no results.

3. **Check database files exist:**
   ```bash
   docker exec mailserver ls -la /tmp/docker-mailserver/*.db
   ```
   Should show `postfix-virtual.cf.db` and `postfix-transport.db`.

4. **Check Rspamd milter:**
   ```bash
   docker logs mailserver | grep "milter"
   ```
   Should show successful milter connections (or graceful handling of unavailability).

## Technical Details

### Postscreen Access List

The postscreen access list is processed in order:
1. First checks `permit_mynetworks` (Docker internal networks)
2. Then checks the CIDR whitelist
3. Whitelisted IPs bypass all postscreen tests including PREGREET detection

### Database Generation

Postfix uses Berkeley DB hash tables for fast lookups:
- `postmap` command generates `.db` files from text files
- Format: `postmap /path/to/file.cf` creates `file.cf.db`
- Must be regenerated whenever the source file changes
- The setup script handles this automatically

### Milter Default Action

The `milter_default_action` setting controls what happens when milter services are unavailable:
- `accept` - Accept mail (graceful degradation)
- `reject` - Reject mail (strict enforcement)
- `tempfail` - Temporarily defer mail

We use `accept` to prevent mail rejection during service startup or temporary outages, while still using Rspamd when available.

## Troubleshooting

### PREGREET violations still occurring

1. Check if the postscreen_access.cidr file is mounted:
   ```bash
   docker exec mailserver cat /tmp/docker-mailserver/postscreen_access.cidr
   ```

2. Verify postfix configuration:
   ```bash
   docker exec mailserver postconf postscreen_access_list
   ```

### Database files not being created

1. Check setup script logs:
   ```bash
   docker logs mailserver | grep SETUP
   ```

2. Manually run the setup script:
   ```bash
   docker exec mailserver bash /usr/local/bin/setup-mailserver.sh
   ```

3. Check file permissions:
   ```bash
   docker exec mailserver ls -la /tmp/docker-mailserver/
   ```

### Milter connection issues persist

1. Check if Rspamd is running:
   ```bash
   docker exec mailserver pgrep rspamd
   ```

2. Check if milter port is listening:
   ```bash
   docker exec mailserver netstat -tuln | grep 11332
   ```

3. View Rspamd logs:
   ```bash
   docker exec mailserver tail -f /var/log/mail/rspamd.log
   ```

## References

- [Postfix Postscreen Documentation](http://www.postfix.org/postscreen.8.html)
- [Postfix CIDR Tables](http://www.postfix.org/cidr_table.5.html)
- [Postfix Milter Configuration](http://www.postfix.org/MILTER_README.html)
- [Docker Mailserver Documentation](https://docker-mailserver.github.io/docker-mailserver/latest/)
