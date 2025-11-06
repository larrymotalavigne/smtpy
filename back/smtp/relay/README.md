# SMTP Relay Service

An async SMTP relay service with connection pooling, queuing, and retry logic for forwarding emails.

## Features

- **Async Operation**: Built on `aiosmtplib` for non-blocking SMTP operations
- **Connection Pooling**: Maintains a pool of SMTP connections for better performance
- **Queue Management**: Email queue with priority support
- **Retry Logic**: Exponential backoff retry mechanism (3 retries by default)
- **Rate Limiting**: Prevents overwhelming relay servers (100 emails/min by default)
- **Error Handling**: Comprehensive error logging and recovery
- **Statistics**: Real-time metrics for monitoring

## Configuration

Configure the relay service via environment variables in `.env` or `.env.production`:

```bash
# SMTP Relay Configuration
SMTP_HOST=smtp.gmail.com          # SMTP server hostname
SMTP_PORT=587                     # SMTP server port
SMTP_USER=your-email@gmail.com    # SMTP username (optional)
SMTP_PASSWORD=your-app-password   # SMTP password (optional)
SMTP_USE_TLS=true                 # Use STARTTLS (recommended)
SMTP_USE_SSL=false                # Use SSL/TLS from start
```

### Relay Service Options

| Option | Default | Description |
|--------|---------|-------------|
| Gmail | smtp.gmail.com:587 | Easiest for testing, requires app password |
| SendGrid | smtp.sendgrid.net:587 | Professional email delivery service |
| Mailgun | smtp.mailgun.org:587 | Reliable transactional email service |
| AWS SES | email-smtp.us-east-1.amazonaws.com:587 | Amazon's email service |

## Usage

### Basic Usage

```python
from smtp.relay import send_email, EmailPriority
from email.message import EmailMessage

# Create email
message = EmailMessage()
message["Subject"] = "Test Email"
message["From"] = "sender@example.com"
message["To"] = "recipient@example.com"
message.set_content("This is a test email")

# Send email (automatically queued)
success = await send_email(
    message=message,
    targets=["recipient@example.com"],
    mail_from="noreply@smtpy.fr",
    priority=EmailPriority.NORMAL
)
```

### Advanced Usage

```python
from smtp.relay import SMTPRelayService, EmailPriority

# Create custom relay service
relay = SMTPRelayService(
    host="smtp.gmail.com",
    port=587,
    username="your-email@gmail.com",
    password="your-app-password",
    use_tls=True,
    pool_size=10,              # Number of SMTP connections
    max_queue_size=1000,       # Maximum emails in queue
    rate_limit=100             # Emails per minute
)

# Start the service
await relay.start(num_workers=5)

# Send email with high priority
await relay.send(
    message=message,
    targets=["important@example.com"],
    mail_from="alerts@smtpy.fr",
    priority=EmailPriority.HIGH
)

# Get statistics
stats = relay.get_stats()
print(f"Sent: {stats['sent']}, Failed: {stats['failed']}, Queued: {stats['queue_size']}")

# Stop the service gracefully
await relay.stop()
```

## Email Priorities

The relay service supports three priority levels:

- `EmailPriority.HIGH` - Sent first, for urgent emails
- `EmailPriority.NORMAL` - Default priority
- `EmailPriority.LOW` - Sent last, for bulk emails

## Retry Logic

Failed emails are automatically retried with exponential backoff:

- **Retry 1**: Wait 2 seconds
- **Retry 2**: Wait 4 seconds
- **Retry 3**: Wait 8 seconds
- **After 3 retries**: Email marked as failed

## Monitoring

### Statistics

The relay service tracks the following metrics:

```python
stats = relay.get_stats()
# Returns:
# {
#     "sent": 150,           # Successfully sent emails
#     "failed": 5,           # Failed emails (after retries)
#     "retried": 8,          # Retry attempts
#     "queued": 3,           # Currently in queue
#     "queue_size": 3,       # Current queue size
#     "pool_size": 5,        # Available connections
#     "running": True        # Service status
# }
```

### Logging

The service logs all operations:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Logs include:
# - Connection pool status
# - Email send attempts
# - Retry attempts
# - Rate limit enforcement
# - Error details
```

## Gmail Configuration

### Step 1: Enable 2-Factor Authentication

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification

### Step 2: Generate App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "SMTPy Relay"
4. Copy the generated password

### Step 3: Configure SMTPy

```bash
# In .env.production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
```

## SendGrid Configuration

### Step 1: Get API Key

1. Sign up at https://sendgrid.com
2. Create an API key with "Mail Send" permissions

### Step 2: Configure SMTPy

```bash
# In .env.production
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
```

## AWS SES Configuration

### Step 1: Create SMTP Credentials

1. Go to AWS SES Console
2. Navigate to "SMTP Settings"
3. Create SMTP credentials

### Step 2: Verify Domain/Email

1. Verify your sending domain or email address
2. Request production access (required for >200 emails/day)

### Step 3: Configure SMTPy

```bash
# In .env.production
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
SMTP_USE_TLS=true
```

## Troubleshooting

### Connection Errors

```
Error: Failed to create SMTP connection
```

**Solutions**:
- Check firewall allows outbound connections on port 587
- Verify SMTP_HOST and SMTP_PORT are correct
- Ensure credentials are valid

### Authentication Errors

```
Error: SMTP authentication failed
```

**Solutions**:
- For Gmail: Use app password, not account password
- For SendGrid: Ensure username is literally "apikey"
- Verify password doesn't have leading/trailing spaces

### Rate Limit Errors

```
Warning: Rate limit reached, waiting 30s
```

**Solutions**:
- Increase `rate_limit` parameter (default: 100/min)
- Upgrade relay service plan for higher limits
- Spread email sending over longer time periods

### Queue Full Errors

```
Error: Email queue full (1000), cannot queue email
```

**Solutions**:
- Increase `max_queue_size` parameter
- Add more workers to process queue faster
- Check if relay service is stuck

## Performance Tuning

### For High Volume

```python
relay = SMTPRelayService(
    pool_size=20,          # More connections
    max_queue_size=5000,   # Larger queue
    rate_limit=500         # Higher rate limit
)
await relay.start(num_workers=10)  # More workers
```

### For Low Latency

```python
relay = SMTPRelayService(
    pool_size=10,
    max_queue_size=100
)
await relay.start(num_workers=5)

# Use HIGH priority for time-sensitive emails
await relay.send(message, targets, priority=EmailPriority.HIGH)
```

## Architecture

```
┌─────────────────┐
│  SMTP Handler   │  Receives emails
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Relay Service  │  Queues & manages
│  ┌───────────┐  │
│  │   Queue   │  │  Priority queue
│  └───────────┘  │
│  ┌───────────┐  │
│  │  Workers  │  │  3-10 workers
│  └───────────┘  │
│  ┌───────────┐  │
│  │   Pool    │  │  5-20 connections
│  └───────────┘  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SMTP Relay     │  Gmail/SendGrid/etc
│  smtp.gmail.com │
└─────────────────┘
```

## Security

- Credentials stored in environment variables, never in code
- TLS/STARTTLS encryption supported
- Connection pooling prevents credential exposure
- Failed auth attempts logged

## Testing

```bash
# Test relay service
cd back/smtp
python -m pytest tests/test_relay_service.py -v

# Manual test
python -c "
import asyncio
from relay import send_email, EmailPriority
from email.message import EmailMessage

async def test():
    msg = EmailMessage()
    msg['Subject'] = 'Test'
    msg['From'] = 'test@example.com'
    msg['To'] = 'recipient@example.com'
    msg.set_content('Test message')

    success = await send_email(msg, ['recipient@example.com'])
    print(f'Success: {success}')

asyncio.run(test())
"
```

## License

Part of SMTPy - MIT License
