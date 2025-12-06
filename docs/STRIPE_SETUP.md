# Stripe Configuration Guide for SMTPy

## Current Status
The `/admin/stripe-config` endpoint is returning a 500 error because Stripe is not properly configured.

## Prerequisites
1. A Stripe account (sign up at https://stripe.com)
2. Access to the server where SMTPy is deployed

## Step 1: Get Your Stripe API Keys

### For Testing (Recommended First)
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your **Secret key** (starts with `sk_test_`)
3. Save it securely - you'll need it for the .env file

### For Production
1. Go to https://dashboard.stripe.com/apikeys
2. Copy your **Secret key** (starts with `sk_live_`)
3. Keep this extremely secure - it provides full access to your Stripe account

## Step 2: Set Up Stripe Webhooks

Stripe webhooks allow Stripe to notify your application when events occur (like successful payments, subscription cancellations, etc.).

1. Go to https://dashboard.stripe.com/webhooks (or https://dashboard.stripe.com/test/webhooks for test mode)
2. Click "Add endpoint"
3. Enter your endpoint URL:
   - For production: `https://api.smtpy.fr/webhooks/stripe`
   - For testing: Use your actual API domain
4. Select the events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Click "Add endpoint"
6. Copy the **Signing secret** (starts with `whsec_`)

## Step 3: Create Environment Configuration

You need to create a `.env.production` file with your Stripe credentials:

```bash
# Copy the template
cp .env.production.template .env.production

# Edit the file and replace the Stripe values:
# STRIPE_API_KEY=sk_test_... (or sk_live_... for production)
# STRIPE_WEBHOOK_SECRET=whsec_...
```

## Step 4: Configure Stripe Settings

Edit your `.env.production` file with these Stripe-specific settings:

```bash
# For Test Mode
STRIPE_API_KEY=sk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
STRIPE_SUCCESS_URL=https://smtpy.fr/billing/success
STRIPE_CANCEL_URL=https://smtpy.fr/billing/cancel
STRIPE_PORTAL_RETURN_URL=https://smtpy.fr/billing

# For Production Mode (when ready)
STRIPE_API_KEY=sk_live_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET_HERE
STRIPE_SUCCESS_URL=https://smtpy.fr/billing/success
STRIPE_CANCEL_URL=https://smtpy.fr/billing/cancel
STRIPE_PORTAL_RETURN_URL=https://smtpy.fr/billing
```

## Step 5: Restart the Services

After updating the .env.production file:

```bash
# Stop the services
docker compose -f docker-compose.prod.yml down

# Start with the new configuration
docker compose -f docker-compose.prod.yml up -d

# Check that the API started successfully
docker compose -f docker-compose.prod.yml logs api
```

## Step 6: Verify Configuration

1. Go to https://smtpy.fr/admin
2. The Stripe configuration section should now show:
   - ✅ API Key Configured: Yes
   - ✅ Mode: test (or live)
   - ✅ Connection Status: Connected
   - ✅ Webhook Secret: Configured

## Troubleshooting

### Error: "Authentication failed"
- Check that your API key is correct
- Verify you're using the right key for test/live mode
- Make sure there are no extra spaces in the .env file

### Error: "Webhook verification failed"
- Check that your webhook secret is correct
- Verify the webhook endpoint URL matches exactly
- Make sure you're using the webhook secret for the correct mode (test/live)

### Error: "Connection test failed"
- Check your internet connection
- Verify Stripe's API is accessible (https://status.stripe.com)
- Check docker logs for more details: `docker compose -f docker-compose.prod.yml logs api`

## Security Best Practices

1. **Never commit** .env.production to git (it's already in .gitignore)
2. **Never share** your secret keys publicly
3. **Use test mode** first to verify everything works
4. **Rotate keys** regularly (every 90 days recommended)
5. **Use restricted API keys** if possible (Stripe allows limiting key permissions)
6. **Monitor** your Stripe dashboard for unusual activity

## Next Steps After Configuration

Once Stripe is configured, you can:
1. Create products and pricing plans in Stripe Dashboard
2. Test the checkout flow at `/billing`
3. Set up subscription tiers for your users
4. Configure tax rates and invoicing
5. Set up customer portal for subscription management

## Need Help?

- Stripe Documentation: https://stripe.com/docs
- Stripe Support: https://support.stripe.com
- SMTPy Issues: https://github.com/larrymotalavigne/smtpy/issues
