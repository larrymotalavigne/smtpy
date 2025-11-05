# Stripe Integration - SMTPy

## ✅ Integration Status: COMPLETE

The Stripe integration for SMTPy billing has been successfully completed and is ready for testing.

## 📋 What's Configured

### 1. Stripe Products Created
Successfully created the following products in your Stripe test account:

- **SMTPy Pro** (Monthly)
  - Product ID: `prod_TMnIFb2FGmLblX`
  - Price ID: `price_1SQ3i1IDKuDXFSH2rfDz6EGx`
  - Amount: €9.00/month
  - Limits: 5 domains, unlimited aliases, 10,000 emails/month

- **SMTPy Entreprise** (Monthly)
  - Product ID: `prod_TMnIIcF4AEffZr`
  - Price ID: `price_1SQ3i2IDKuDXFSH2ZVtCqL2f`
  - Amount: Custom pricing
  - Limits: Unlimited domains, aliases, and emails

### 2. API Keys Configured
✅ **Test Mode** - Currently configured
- API Key: `sk_test_51Ry6LCIDKuDXFSH2cfvF6MyslgVht2kdPzLAYOkLAuOIDc0dA8QuNJQh5VCoWUqPIDjUAReQ0dJLkI8i7NHerTnb009Jz8pyQc`
- Configured in:
  - `/back/.env` (development)
  - `/.env.production` (production - to be replaced with live key)

⏳ **Live Mode** - Pending deployment
- Replace test key with live key from: https://dashboard.stripe.com/apikeys
- Update both `.env` and `.env.production` files

### 3. Backend Endpoints Configured

#### Billing Endpoints (`/billing`)
- ✅ `POST /billing/checkout-session` - Create Stripe checkout session
- ✅ `GET /billing/customer-portal` - Get Stripe customer portal URL
- ✅ `GET /billing/organization` - Get organization billing info
- ✅ `GET /billing/subscription` - Get current subscription
- ✅ `GET /billing/plans` - List available plans (with real price IDs)
- ✅ `GET /billing/usage-limits` - Get usage and limits

#### Webhook Endpoint (`/webhooks`)
- ✅ `POST /webhooks/stripe` - Handle Stripe webhook events
- ⚠️ Webhook secret needs configuration after deployment

### 4. Redirect URLs Configured
- Success: `http://localhost:4200/billing?success=true` (dev) / `https://smtpy.fr/billing?success=true` (prod)
- Cancel: `http://localhost:4200/billing?canceled=true` (dev) / `https://smtpy.fr/billing?canceled=true` (prod)
- Portal Return: `http://localhost:4200/billing` (dev) / `https://smtpy.fr/billing` (prod)

### 5. Frontend Integration
- ✅ Billing component displays plans with real Stripe price IDs
- ✅ Currency formatting in EUR (French locale)
- ✅ Checkout flow redirects to Stripe
- ✅ Customer portal integration
- ✅ Subscription status display
- ✅ Usage limits visualization

## 🧪 Testing Flow

### Local Development Testing
1. Start backend: `cd back && uvicorn api.main:app --reload`
2. Start frontend: `cd front && npm start`
3. Navigate to http://localhost:4200/billing
4. Click "Souscrire" on Pro plan
5. Use Stripe test card: `4242 4242 4242 4242`
6. Complete checkout and verify subscription activation

### Stripe Test Cards
- **Success**: `4242 4242 4242 4242`
- **Requires authentication**: `4000 0025 0000 3155`
- **Declined**: `4000 0000 0000 9995`
- Any future expiry date (e.g., 12/34)
- Any 3-digit CVC

## ⚠️ Pending Configuration

### 1. Webhook Secret (After Deployment)
After deploying to production:

1. Go to https://dashboard.stripe.com/webhooks
2. Create endpoint: `https://api.smtpy.fr/webhooks/stripe`
3. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the webhook signing secret
5. Update environment variables:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret
   ```
6. Restart the API service

### 2. Live API Keys (Before Production Launch)
Replace test keys with live keys:

1. Get live API key from: https://dashboard.stripe.com/apikeys
2. Update `.env.production`:
   ```bash
   STRIPE_API_KEY=sk_live_your_actual_live_key
   ```
3. Update webhook secret with live mode webhook
4. Test thoroughly in live mode before announcement

## 📊 Supported Events

The webhook handler (`/webhooks/stripe`) processes:
- `checkout.session.completed` - New subscription created
- `customer.subscription.updated` - Subscription changed
- `customer.subscription.deleted` - Subscription cancelled
- `invoice.payment_succeeded` - Payment successful
- `invoice.payment_failed` - Payment failed

## 🔒 Security Notes

1. **Webhook Signature Verification**: All webhook events are cryptographically verified
2. **Authentication Required**: All billing endpoints require authenticated session
3. **Organization Isolation**: Users can only access their own organization's billing
4. **Test Mode**: Currently using test keys - no real charges will occur
5. **HTTPS Required**: Webhooks require HTTPS in production (enforced by Stripe)

## 📁 Key Files

### Backend
- `/back/api/views/billing_view.py` - Billing endpoints with price IDs
- `/back/api/views/webhooks_view.py` - Webhook handler
- `/back/api/controllers/billing_controller.py` - Business logic
- `/back/api/services/stripe_service.py` - Stripe API wrapper
- `/back/scripts/setup_stripe_products.py` - Product creation script
- `/back/.env` - Development configuration
- `/.env.production` - Production configuration

### Frontend
- `/front/src/app/pages/billing/billing.component.ts` - Billing page
- `/front/src/app/pages/service/billing-api.service.ts` - API client

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] Replace `STRIPE_API_KEY` with live key in `.env.production`
- [ ] Configure webhook endpoint at https://dashboard.stripe.com/webhooks
- [ ] Update `STRIPE_WEBHOOK_SECRET` in `.env.production`
- [ ] Verify redirect URLs point to production frontend (https://smtpy.fr)
- [ ] Test checkout flow in test mode
- [ ] Test webhook events in test mode (using Stripe CLI or dashboard)
- [ ] Verify customer portal access
- [ ] Test subscription cancellation flow
- [ ] Monitor webhook delivery in Stripe dashboard
- [ ] Set up Stripe email notifications for failed payments
- [ ] Configure Stripe billing portal settings

## 📞 Support Resources

- Stripe Dashboard: https://dashboard.stripe.com
- Stripe Test Mode: https://dashboard.stripe.com/test
- Stripe API Docs: https://stripe.com/docs/api
- Webhook Testing: https://stripe.com/docs/webhooks/test
- Test Cards: https://stripe.com/docs/testing

## ✨ Ready for Testing

The integration is **complete and ready for end-to-end testing**. All backend endpoints are configured with real Stripe price IDs, the frontend is integrated, and the webhook handler is prepared.

Next steps:
1. Test the complete checkout flow locally
2. Verify subscription activation
3. Test customer portal access
4. Configure production webhook after deployment
5. Replace with live API keys before production launch
