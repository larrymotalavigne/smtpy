# Mailserver Configuration

This directory contains configuration files for the docker-mailserver integration with SMTPy.

## Files

- **user-patches.sh**: Automatically executed by docker-mailserver on startup to generate Postfix database files
- **postfix-main.cf**: Custom Postfix main configuration (extends docker-mailserver defaults)
- **postfix-virtual.cf**: Virtual alias mappings for email addresses
- **postfix-transport**: Transport maps for routing emails to SMTPy SMTP receiver
- **postscreen_access.cidr**: Postscreen whitelist for health checks and trusted networks

## Setup Process

The `user-patches.sh` script automatically runs on container startup and:

1. Waits for Postfix to be ready
2. Compiles `postfix-virtual.cf` to `postfix-virtual.cf.db` using `postmap`
3. Compiles `postfix-transport` to `postfix-transport.db` using `postmap`
4. Reloads Postfix to apply the changes
5. Waits for Rspamd and ClamAV to initialize

## Troubleshooting

### Missing .db files error

If you see errors like:
```
error: open database /tmp/docker-mailserver/postfix-virtual.cf.db: No such file or directory
```

**Solution 1: Wait for startup**
The user-patches.sh script runs automatically. Wait 1-2 minutes for it to complete.

**Solution 2: Manual execution**
If the script didn't run, execute it manually:
```bash
docker exec mailserver /tmp/docker-mailserver/user-patches.sh
```

**Solution 3: Restart container**
```bash
docker restart mailserver
```

### Verify database files exist

```bash
docker exec mailserver ls -la /tmp/docker-mailserver/*.db
```

You should see:
- `postfix-virtual.cf.db`
- `postfix-transport.db`

### Check mailserver health

```bash
docker exec mailserver /usr/local/bin/healthcheck.sh
```

### View mailserver logs

```bash
docker logs mailserver --tail 100 -f
```

## Adding Email Aliases

Edit `postfix-virtual.cf` to add virtual aliases, then regenerate the database:

```bash
# Edit the file
nano config/mailserver/postfix-virtual.cf

# Regenerate database (automatic on restart, or manual)
docker exec mailserver postmap /tmp/docker-mailserver/postfix-virtual.cf
docker exec mailserver postfix reload
```

## Routing Emails to SMTPy

Edit `postfix-transport` to route specific addresses to SMTPy:

```bash
# Edit the file
nano config/mailserver/postfix-transport

# Add a line like:
# myalias@atomdev.fr       smtp:[smtpy-smtp-receiver]:2525

# Regenerate database
docker exec mailserver postmap /tmp/docker-mailserver/postfix-transport
docker exec mailserver postfix reload
```

## SSL/TLS Setup

The mailserver currently runs without SSL (`SSL_TYPE=`). To enable SSL:

1. Ensure Let's Encrypt certificates are available in the `npm_letsencrypt` volume
2. Set `MAILSERVER_SSL_TYPE=letsencrypt` in `.env.production`
3. Restart the mailserver: `docker restart mailserver`

## References

- [docker-mailserver documentation](https://docker-mailserver.github.io/docker-mailserver/latest/)
- [Postfix Virtual Alias Domains](http://www.postfix.org/virtual.5.html)
- [Postfix Transport Maps](http://www.postfix.org/transport.5.html)
- [User Patches](https://docker-mailserver.github.io/docker-mailserver/latest/config/advanced/override-defaults/user-patches/)
