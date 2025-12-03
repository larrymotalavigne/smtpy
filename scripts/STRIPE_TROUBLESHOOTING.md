# Stripe Troubleshooting Guide

This guide helps you diagnose and fix common Stripe configuration issues in SMTPy v2.

## Quick Start

Run the troubleshooting script:

```bash
# From the project root
python scripts/troubleshoot-stripe.py

# Or with uv
uv run scripts/troubleshoot-stripe.py

# Or directly (if executable)
./scripts/troubleshoot-stripe.py
```

## What the Script Checks

The troubleshooting script performs 8 comprehensive checks:

1. **Configuration Check** - Verifies all Stripe-related environment variables are set
2. **API Key Format Check** - Validates your STRIPE_API_KEY format and type
3. **Webhook Secret Check** - Ensures STRIPE_WEBHOOK_SECRET is properly configured
4. **API Connectivity Test** - Tests connection to Stripe API and retrieves account info
5. **Products and Prices Check** - Lists all active products and prices in your account
6. **Verify Application Price IDs** - Checks if hardcoded price IDs exist in your Stripe account
7. **Customer Creation Test** - Tests creating and deleting a test customer
8. **Webhook Configuration Check** - Verifies webhook endpoints are configured

## Common Issues and Solutions

### Issue 1: Missing or Invalid API Key

**Symptoms:**
- `STRIPE_API_KEY is not set or empty`
- `Authentication failed`

**Solution:**
1. Go to [Stripe Dashboard > API Keys](https://dashboard.stripe.com/apikeys)
2. Copy your Secret key (starts with `sk_test_` or `sk_live_`)
3. Add to your `.env` file:
   ```
   STRIPE_API_KEY=sk_test_your_key_here
   ```
4. **Never** use the Publishable key (pk_) for backend configuration

### Issue 2: Wrong API Key Type

**Symptoms:**
- `API key appears to be a publishable key (pk_)`

**Solution:**
- You need the **Secret key** (sk_), not the Publishable key (pk_)
- The Secret key should only be used on the server side
- The Publishable key is for client-side/frontend use

### Issue 3: Missing Webhook Secret

**Symptoms:**
- `STRIPE_WEBHOOK_SECRET is not set or empty`
- Webhook events fail with signature verification errors

**Solution:**
1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Add your webhook URL: `https://your-domain.com/api/webhooks/stripe`
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the "Signing secret" (starts with `whsec_`)
6. Add to your `.env` file:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
   ```

### Issue 4: Invalid Price IDs

**Symptoms:**
- `Invalid: price_xxx - Not found in Stripe account`
- Checkout sessions fail to create

**Solution:**
1. Create products and prices in [Stripe Dashboard > Products](https://dashboard.stripe.com/products)
2. Copy the Price IDs from your products
3. Update the price IDs in `back/api/views/billing_view.py`:
   ```python
   {
       "price_id": "price_YOUR_ACTUAL_PRICE_ID",
       "name": "Pro",
       # ...
   }
   ```

### Issue 5: Network Connectivity Issues

**Symptoms:**
- `Network error connecting to Stripe`
- `APIConnectionError`

**Solution:**
1. Check your internet connection
2. Verify firewall isn't blocking `api.stripe.com`
3. If using a proxy, configure it properly
4. Check if DNS is resolving correctly: `nslookup api.stripe.com`

### Issue 6: Test vs Live Mode Mismatch

**Symptoms:**
- Data created in test mode not visible in live mode (or vice versa)
- Different API keys return different results

**Solution:**
- Stripe has separate **test mode** and **live mode**
- Test mode keys: `sk_test_...`
- Live mode keys: `sk_live_...`
- Make sure you're using the right mode for your environment:
  - Development: Use test mode keys
  - Production: Use live mode keys
- Price IDs, products, and customers are **separate** between modes

### Issue 7: Incorrect URL Configuration

**Symptoms:**
- After checkout, user is redirected to wrong URL
- Portal doesn't return to the right page

**Solution:**
Update these in your `.env` file to match your actual URLs:
```
STRIPE_SUCCESS_URL=https://your-domain.com/billing/success
STRIPE_CANCEL_URL=https://your-domain.com/billing/cancel
STRIPE_PORTAL_RETURN_URL=https://your-domain.com/billing
```

For local development:
```
STRIPE_SUCCESS_URL=http://localhost:4200/billing/success
STRIPE_CANCEL_URL=http://localhost:4200/billing/cancel
STRIPE_PORTAL_RETURN_URL=http://localhost:4200/billing
```

## Environment Variables Reference

Required Stripe environment variables:

```bash
# Required - Secret API Key from Stripe Dashboard
STRIPE_API_KEY=sk_test_...

# Required for webhooks - Webhook signing secret
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional - URLs for checkout flow (defaults shown)
STRIPE_SUCCESS_URL=http://localhost:8000/billing/success
STRIPE_CANCEL_URL=http://localhost:8000/billing/cancel
STRIPE_PORTAL_RETURN_URL=http://localhost:8000/billing
```

## Testing Your Configuration

### Manual Test: Create a Customer

```python
import stripe
stripe.api_key = "sk_test_..."

customer = stripe.Customer.create(
    email="test@example.com",
    name="Test Customer"
)
print(f"Created customer: {customer.id}")
```

### Manual Test: List Prices

```python
import stripe
stripe.api_key = "sk_test_..."

prices = stripe.Price.list(limit=10)
for price in prices:
    print(f"Price ID: {price.id}")
```

### Manual Test: Verify Webhook

```bash
# Use Stripe CLI to forward webhooks to local development
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Trigger a test event
stripe trigger checkout.session.completed
```

## Additional Resources

- **Stripe Dashboard**: https://dashboard.stripe.com
- **API Keys**: https://dashboard.stripe.com/apikeys
- **Webhooks**: https://dashboard.stripe.com/webhooks
- **Products**: https://dashboard.stripe.com/products
- **Logs**: https://dashboard.stripe.com/logs (great for debugging)
- **Test Cards**: https://stripe.com/docs/testing
- **API Documentation**: https://stripe.com/docs/api
- **Stripe CLI**: https://stripe.com/docs/stripe-cli

## Getting Help

If the troubleshooting script doesn't resolve your issue:

1. Check the **Stripe logs** in your dashboard for detailed error messages
2. Review the **application logs** for API errors
3. Test with Stripe's **test mode** and test card numbers first
4. Use the **Stripe CLI** for local webhook testing
5. Consult the Stripe documentation for specific error codes

## Stripe CLI Installation (Optional but Recommended)

The Stripe CLI is helpful for local development and webhook testing:

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Linux
# Download from: https://github.com/stripe/stripe-cli/releases

# Login
stripe login

# Forward webhooks to local development
stripe listen --forward-to http://localhost:8000/api/webhooks/stripe
```

## Script Output Example

```
============================================================
Stripe Configuration Troubleshooting
============================================================

✓ Configuration values loaded
✓ API key format is valid (Test mode)
✓ Connected to Stripe account: acct_xxx (user@example.com)
✓ Found 3 active price(s)
✓ All configured price IDs are valid
✓ Successfully created and deleted test customer
⚠ No webhook endpoints configured

Diagnostics completed!
```
