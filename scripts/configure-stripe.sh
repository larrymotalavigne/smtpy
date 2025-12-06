#!/bin/bash
# SMTPy Stripe Configuration Helper Script
# This script helps you configure Stripe for your SMTPy installation

set -e

echo "================================================="
echo "SMTPy Stripe Configuration Helper"
echo "================================================="
echo ""

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create it first from the template:"
    echo "  cp .env.production.template .env.production"
    exit 1
fi

echo "📋 Current Stripe Configuration Status:"
echo ""

# Check current values
CURRENT_API_KEY=$(grep "^STRIPE_API_KEY=" .env.production | cut -d'=' -f2)
CURRENT_WEBHOOK_SECRET=$(grep "^STRIPE_WEBHOOK_SECRET=" .env.production | cut -d'=' -f2)

if [[ "$CURRENT_API_KEY" == *"PLACEHOLDER"* ]] || [[ "$CURRENT_API_KEY" == *"REPLACE"* ]]; then
    echo "  API Key: ❌ Not configured (placeholder value)"
    NEEDS_CONFIG=true
else
    # Mask the key for security
    MASKED_KEY="${CURRENT_API_KEY:0:10}...${CURRENT_API_KEY: -4}"
    echo "  API Key: ✅ Configured ($MASKED_KEY)"
fi

if [[ "$CURRENT_WEBHOOK_SECRET" == *"PLACEHOLDER"* ]] || [[ "$CURRENT_WEBHOOK_SECRET" == *"REPLACE"* ]]; then
    echo "  Webhook Secret: ❌ Not configured (placeholder value)"
    NEEDS_CONFIG=true
else
    MASKED_SECRET="${CURRENT_WEBHOOK_SECRET:0:10}...${CURRENT_WEBHOOK_SECRET: -4}"
    echo "  Webhook Secret: ✅ Configured ($MASKED_SECRET)"
fi

echo ""
echo "================================================="
echo ""

if [ "$NEEDS_CONFIG" = true ]; then
    echo "⚠️  Stripe is not fully configured!"
    echo ""
    echo "To configure Stripe, you need:"
    echo ""
    echo "1. A Stripe API Key (starts with sk_test_ or sk_live_)"
    echo "   Get it from: https://dashboard.stripe.com/test/apikeys"
    echo ""
    echo "2. A Stripe Webhook Secret (starts with whsec_)"
    echo "   Get it from: https://dashboard.stripe.com/webhooks"
    echo "   Webhook URL: https://api.smtpy.fr/webhooks/stripe"
    echo ""
    echo "See STRIPE_SETUP.md for detailed instructions."
    echo ""

    read -p "Do you want to configure Stripe now? (y/n): " CONFIGURE_NOW

    if [[ "$CONFIGURE_NOW" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Enter your Stripe API Key:"
        read -r NEW_API_KEY

        echo "Enter your Stripe Webhook Secret:"
        read -r NEW_WEBHOOK_SECRET

        # Validate format
        if [[ ! "$NEW_API_KEY" =~ ^sk_(test|live)_ ]]; then
            echo "❌ Error: API Key should start with 'sk_test_' or 'sk_live_'"
            exit 1
        fi

        if [[ ! "$NEW_WEBHOOK_SECRET" =~ ^whsec_ ]]; then
            echo "❌ Error: Webhook Secret should start with 'whsec_'"
            exit 1
        fi

        # Update .env.production
        sed -i "s|^STRIPE_API_KEY=.*|STRIPE_API_KEY=$NEW_API_KEY|" .env.production
        sed -i "s|^STRIPE_WEBHOOK_SECRET=.*|STRIPE_WEBHOOK_SECRET=$NEW_WEBHOOK_SECRET|" .env.production

        echo ""
        echo "✅ Stripe configuration updated in .env.production"
        echo ""

        read -p "Do you want to restart the services now? (y/n): " RESTART_NOW

        if [[ "$RESTART_NOW" =~ ^[Yy]$ ]]; then
            echo ""
            echo "Restarting services..."
            docker compose -f docker-compose.prod.yml restart api
            echo ""
            echo "✅ Services restarted!"
            echo ""
            echo "Please check https://smtpy.fr/admin to verify Stripe configuration."
        else
            echo ""
            echo "⚠️  Remember to restart services for changes to take effect:"
            echo "  docker compose -f docker-compose.prod.yml restart api"
        fi
    else
        echo ""
        echo "Configuration cancelled. You can edit .env.production manually."
        echo "Then restart services: docker compose -f docker-compose.prod.yml restart api"
    fi
else
    echo "✅ Stripe is already configured!"
    echo ""
    echo "To verify the configuration, visit: https://smtpy.fr/admin"
    echo ""
    read -p "Do you want to restart services to apply any changes? (y/n): " RESTART_NOW

    if [[ "$RESTART_NOW" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Restarting services..."
        docker compose -f docker-compose.prod.yml restart api
        echo "✅ Services restarted!"
    fi
fi

echo ""
echo "================================================="
echo "Configuration complete!"
echo "================================================="
