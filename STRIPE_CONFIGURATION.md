# Stripe Configuration Guide for SMTPY

This guide explains how to properly configure Stripe for the SMTPY application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Stripe Account Setup](#stripe-account-setup)
3. [API Keys Configuration](#api-keys-configuration)
4. [Webhook Configuration](#webhook-configuration)
5. [Environment Variables](#environment-variables)
6. [Testing Configuration](#testing-configuration)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- A Stripe account (sign up at https://stripe.com)
- Access to your Stripe Dashboard
- Admin access to your SMTPY deployment
- Access to your server's environment configuration

---

## Stripe Account Setup

### 1. Create a Stripe Account

1. Go to https://stripe.com and sign up
2. Complete your business profile
3. Verify your email address

### 2. Create Products and Prices

1. Navigate to **Products** in the Stripe Dashboard
2. Click **Add Product**
3. Create your subscription plans with the following details:
   - **Product Name**: e.g., "SMTPY Pro", "SMTPY Business"
   - **Description**: Brief description of the plan
   - **Pricing Model**: Recurring
   - **Billing Period**: Monthly or Yearly
   - **Price**: Set your pricing

4. **Important**: Copy the **Price ID** (starts with `price_`) - you'll need this for your application

### 3. Enable Customer Portal (Optional but Recommended)

1. Go to **Settings** → **Billing** → **Customer Portal**
2. Enable the portal
3. Configure which features customers can manage:
   - ✅ Update payment method
   - ✅ Cancel subscription
   - ✅ View invoices
   - ✅ Switch plans (if you have multiple)

---

## API Keys Configuration

### Test Mode vs Live Mode

Stripe provides two environments:
- **Test Mode**: For development and testing (uses test API keys)
- **Live Mode**: For production (uses live API keys)

### Getting Your API Keys

#### For Development (Test Mode):

1. In Stripe Dashboard, ensure you're in **Test Mode** (toggle in top right)
2. Go to **Developers** → **API Keys**
3. Copy your keys:
   - **Publishable key**: `pk_test_...` (not used in backend, but may be needed for frontend)
   - **Secret key**: `sk_test_...` ⚠️ **Keep this secure!**

#### For Production (Live Mode):

1. Switch to **Live Mode** in Stripe Dashboard
2. Go to **Developers** → **API Keys**
3. Copy your keys:
   - **Publishable key**: `pk_live_...`
   - **Secret key**: `sk_live_...` ⚠️ **Keep this secure!**

⚠️ **Security Warning**: Never commit API keys to version control or expose them in client-side code!

---

## Webhook Configuration

Webhooks allow Stripe to notify your application about events (payments, subscription changes, etc.)

### 1. Create a Webhook Endpoint

1. Go to **Developers** → **Webhooks** in Stripe Dashboard
2. Click **Add Endpoint**
3. Enter your endpoint URL:
   - **Development**: `https://your-dev-domain.com/webhooks/stripe`
   - **Production**: `https://smtpy.fr/webhooks/stripe`

### 2. Select Events to Listen To

Select the following events (minimum required):

**Subscription Events:**
- ✅ `customer.subscription.created`
- ✅ `customer.subscription.updated`
- ✅ `customer.subscription.deleted`
- ✅ `customer.subscription.trial_will_end`

**Payment Events:**
- ✅ `invoice.payment_succeeded`
- ✅ `invoice.payment_failed`
- ✅ `invoice.finalized`

**Customer Events:**
- ✅ `customer.created`
- ✅ `customer.updated`
- ✅ `customer.deleted`

### 3. Get Your Webhook Signing Secret

1. After creating the webhook, click on it
2. Click **Reveal** under "Signing secret"
3. Copy the secret (starts with `whsec_...`)
4. Save this for your environment configuration

### 4. Test Your Webhook (Development)

For local development, use the Stripe CLI:

```bash
# Install Stripe CLI
# macOS
brew install stripe/stripe-cli/stripe

# Linux
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.4/stripe_1.19.4_linux_x86_64.tar.gz
tar -xvf stripe_1.19.4_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/

# Login to Stripe
stripe login

# Forward webhooks to your local server
stripe listen --forward-to http://localhost:8000/webhooks/stripe

# Trigger test events
stripe trigger customer.subscription.created
```

---

## Environment Variables

### Required Environment Variables

Add these to your `.env` file (or `.env.production` for production):

```bash
# Stripe API Configuration
# Use sk_test_* for development, sk_live_* for production
STRIPE_API_KEY=sk_test_YOUR_TEST_KEY_HERE

# Webhook secret from Stripe Dashboard
# Use whsec_* from your webhook endpoint configuration
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Redirect URLs (adjust based on your domain)
# Where users go after successful checkout
STRIPE_SUCCESS_URL=https://smtpy.fr/billing/success

# Where users go if they cancel checkout
STRIPE_CANCEL_URL=https://smtpy.fr/billing/cancel

# Where users return after managing billing in customer portal
STRIPE_PORTAL_RETURN_URL=https://smtpy.fr/billing
```

### Development Environment Example

```bash
# .env.development
STRIPE_API_KEY=sk_test_YOUR_TEST_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
STRIPE_SUCCESS_URL=http://localhost:4200/billing/success
STRIPE_CANCEL_URL=http://localhost:4200/billing/cancel
STRIPE_PORTAL_RETURN_URL=http://localhost:4200/billing
```

### Production Environment Example

```bash
# .env.production
STRIPE_API_KEY=sk_live_YOUR_LIVE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
STRIPE_SUCCESS_URL=https://smtpy.fr/billing/success
STRIPE_CANCEL_URL=https://smtpy.fr/billing/cancel
STRIPE_PORTAL_RETURN_URL=https://smtpy.fr/billing
```

---

## Testing Configuration

### 1. Verify API Key is Loaded

Check your application logs when starting the backend:

```bash
# You should see:
INFO: Stripe API Key is set (mode: test)
# or
INFO: Stripe API Key is set (mode: live)
```

### 2. Test with Stripe Test Cards

Use these test card numbers in **Test Mode**:

| Card Number | Description |
|-------------|-------------|
| `4242 4242 4242 4242` | Successful payment |
| `4000 0000 0000 0002` | Card declined |
| `4000 0000 0000 9995` | Card with insufficient funds |
| `4000 0025 0000 3155` | Requires 3D Secure authentication |

- **Expiry**: Use any future date (e.g., `12/34`)
- **CVC**: Any 3 digits (e.g., `123`)
- **ZIP**: Any 5 digits (e.g., `12345`)

### 3. Test Subscription Flow

1. Create a test user in your application
2. Navigate to billing/subscription page
3. Click "Subscribe" or "Upgrade"
4. Use a test card to complete checkout
5. Verify:
   - User is redirected to success URL
   - Database shows `stripe_customer_id` and `stripe_subscription_id`
   - Subscription status is `ACTIVE` or `TRIALING`

### 4. Test Webhook Events

Using Stripe CLI:

```bash
# Trigger a subscription created event
stripe trigger customer.subscription.created

# Trigger a payment succeeded event
stripe trigger invoice.payment_succeeded

# Trigger a subscription cancellation
stripe trigger customer.subscription.deleted
```

Verify in your application logs that webhooks are received and processed.

### 5. Use the Admin Dashboard

After implementing the Stripe Configuration panel (see below), you can:
1. Log in as an admin user
2. Navigate to Admin Dashboard
3. Check the "Stripe Configuration" panel
4. Verify all configuration items show ✅ (green checkmark)

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Switch to **Live Mode** in Stripe Dashboard
- [ ] Update `STRIPE_API_KEY` to use `sk_live_*` key
- [ ] Create webhook endpoint for production URL
- [ ] Update `STRIPE_WEBHOOK_SECRET` with production webhook secret
- [ ] Update all `STRIPE_*_URL` variables to production URLs
- [ ] Test webhook delivery from Stripe Dashboard
- [ ] Verify SSL/HTTPS is enabled on your domain
- [ ] Configure DNS properly for your production domain

### Deployment Steps

1. **Update Environment Variables**:
   ```bash
   # On your production server
   nano /path/to/smtpy/.env.production
   # Update all STRIPE_* variables
   ```

2. **Restart Backend Service**:
   ```bash
   # If using Docker
   docker-compose restart backend

   # If using systemd
   sudo systemctl restart smtpy-backend
   ```

3. **Verify Configuration**:
   - Check backend logs for Stripe initialization
   - Access Admin Dashboard and check Stripe Configuration panel
   - All items should show green checkmarks

4. **Test Live Webhook**:
   - Go to Stripe Dashboard → Developers → Webhooks
   - Click on your production webhook
   - Click "Send test webhook"
   - Select an event type
   - Verify it's received in your application logs

5. **Test Live Checkout** (Small Amount):
   - Create a test subscription with a real card
   - Use a small amount or a free trial
   - Verify the full flow works
   - Cancel the test subscription immediately

### Monitoring

Monitor these in production:
- Stripe Dashboard → Developers → Events (for webhook delivery)
- Application logs for Stripe errors
- Admin Dashboard Stripe Configuration panel
- Database for subscription status updates

---

## Troubleshooting

### API Key Issues

**Problem**: "Stripe API Key is not set" warning

**Solution**:
1. Verify `.env` file has `STRIPE_API_KEY=sk_...`
2. Restart backend service
3. Check environment variable is loaded: `echo $STRIPE_API_KEY`

**Problem**: "Invalid API Key" error

**Solution**:
1. Verify you're using the correct key format: `sk_test_*` or `sk_live_*`
2. Check for extra spaces or newlines in the key
3. Regenerate the key in Stripe Dashboard if corrupted

### Webhook Issues

**Problem**: Webhooks not being received

**Solution**:
1. Verify webhook URL is accessible from internet
2. Check firewall allows incoming connections
3. Ensure URL uses HTTPS (required by Stripe in production)
4. Check Stripe Dashboard → Webhooks → View logs for errors

**Problem**: "Webhook signature verification failed"

**Solution**:
1. Verify `STRIPE_WEBHOOK_SECRET` matches the one in Stripe Dashboard
2. Check for extra spaces or newlines in the secret
3. Ensure you're using the correct webhook endpoint's secret
4. Restart backend after updating the secret

### Subscription Issues

**Problem**: Subscription created but not reflected in database

**Solution**:
1. Check webhook is configured and working
2. Verify `customer.subscription.created` event is selected
3. Check application logs for webhook processing errors
4. Manually check Stripe Dashboard for subscription status

**Problem**: Customer portal not working

**Solution**:
1. Enable Customer Portal in Stripe Dashboard
2. Verify `STRIPE_PORTAL_RETURN_URL` is set
3. Check user has `stripe_customer_id` in database

### Test Mode vs Live Mode Issues

**Problem**: Using test key in production or vice versa

**Solution**:
1. Check the key prefix:
   - Test: `sk_test_*`
   - Live: `sk_live_*`
2. Update environment variable to match your environment
3. Verify Admin Dashboard shows correct mode

---

## Admin Dashboard Stripe Configuration Panel

Once the Stripe Configuration panel is implemented, you'll see:

### Configuration Checks

- **API Key Status**: Shows if key is configured and valid
- **Key Mode**: Test or Live mode indicator
- **Webhook Secret**: Verification that secret is configured
- **Webhook URL**: The configured webhook endpoint
- **Success URL**: Checkout success redirect
- **Cancel URL**: Checkout cancel redirect
- **Portal URL**: Customer portal return URL
- **Connection Test**: Real-time API connectivity test
- **Recent Events**: Last 5 webhook events received

### Status Indicators

- ✅ **Green**: Configuration is valid and working
- ⚠️ **Yellow**: Configuration exists but may have issues
- ❌ **Red**: Configuration is missing or invalid

---

## Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe Security Best Practices](https://stripe.com/docs/security/guide)

---

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review Stripe Dashboard → Events → Logs
3. Check application logs for errors
4. Use the Admin Dashboard Stripe Configuration panel
5. Contact Stripe Support for Stripe-specific issues

---

**Last Updated**: December 2025
