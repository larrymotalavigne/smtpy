#!/usr/bin/env python3
"""
Stripe Configuration Troubleshooting Script for SMTPy v2

This script helps diagnose and troubleshoot Stripe configuration issues by:
- Verifying API key configuration and validity
- Testing connectivity to Stripe API
- Validating webhook configuration
- Checking price IDs and products
- Testing customer creation
- Verifying subscription operations
"""

import sys
import os
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back'))

import stripe
from shared.core.config import SETTINGS

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_api_key_format() -> Tuple[bool, str]:
    """Check if the API key is properly formatted."""
    api_key = SETTINGS.STRIPE_API_KEY

    if not api_key:
        return False, "STRIPE_API_KEY is not set or empty"

    if api_key == "":
        return False, "STRIPE_API_KEY is empty"

    # Check if it starts with sk_ (secret key) or pk_ (publishable key)
    if not api_key.startswith("sk_"):
        if api_key.startswith("pk_"):
            return False, "API key appears to be a publishable key (pk_). You need a secret key (sk_)"
        return False, "API key doesn't start with 'sk_'. It should be a secret key"

    # Check if it's test or live mode
    if api_key.startswith("sk_test_"):
        return True, "Test mode API key detected (sk_test_...)"
    elif api_key.startswith("sk_live_"):
        return True, "Live mode API key detected (sk_live_...)"
    else:
        return False, "Unrecognized API key format"

def check_webhook_secret_format() -> Tuple[bool, str]:
    """Check if the webhook secret is properly formatted."""
    webhook_secret = SETTINGS.STRIPE_WEBHOOK_SECRET

    if not webhook_secret:
        return False, "STRIPE_WEBHOOK_SECRET is not set or empty (webhooks will fail)"

    if not webhook_secret.startswith("whsec_"):
        return False, "Webhook secret doesn't start with 'whsec_'"

    return True, "Webhook secret format is valid"

async def test_api_connectivity() -> Tuple[bool, str]:
    """Test connectivity to Stripe API."""
    try:
        # Initialize Stripe
        stripe.api_key = SETTINGS.STRIPE_API_KEY

        # Try to retrieve account information
        account = stripe.Account.retrieve()

        return True, f"Connected to Stripe account: {account.id} ({account.email or 'No email'})"
    except stripe.error.AuthenticationError as e:
        return False, f"Authentication failed: {str(e)}"
    except stripe.error.PermissionError as e:
        return False, f"Permission denied: {str(e)}"
    except stripe.error.APIConnectionError as e:
        return False, f"Network error connecting to Stripe: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

async def check_products_and_prices() -> Tuple[bool, str, List[Dict]]:
    """Check available products and prices."""
    try:
        stripe.api_key = SETTINGS.STRIPE_API_KEY

        # Get all prices
        prices = stripe.Price.list(limit=10, active=True)

        if not prices.data:
            return False, "No active prices found in Stripe account", []

        price_info = []
        for price in prices.data:
            # Get product details
            product = stripe.Product.retrieve(price.product)

            price_info.append({
                "price_id": price.id,
                "product_name": product.name,
                "amount": price.unit_amount,
                "currency": price.currency,
                "interval": price.recurring.interval if price.recurring else "one-time",
                "active": price.active
            })

        return True, f"Found {len(prices.data)} active price(s)", price_info
    except Exception as e:
        return False, f"Error retrieving prices: {str(e)}", []

async def test_customer_creation() -> Tuple[bool, str]:
    """Test creating a test customer."""
    try:
        stripe.api_key = SETTINGS.STRIPE_API_KEY

        test_email = f"test-{datetime.now().timestamp()}@smtpy-test.local"

        # Create a test customer
        customer = stripe.Customer.create(
            email=test_email,
            name="SMTPy Test Customer",
            metadata={
                "source": "smtpy-troubleshoot-script",
                "test": "true"
            }
        )

        # Delete the test customer
        stripe.Customer.delete(customer.id)

        return True, f"Successfully created and deleted test customer: {customer.id}"
    except Exception as e:
        return False, f"Error creating test customer: {str(e)}"

async def verify_price_ids() -> Tuple[bool, str, List[str]]:
    """Verify the price IDs used in the application."""
    try:
        stripe.api_key = SETTINGS.STRIPE_API_KEY

        # Price IDs from billing_view.py
        price_ids = [
            "price_1SQ3i1IDKuDXFSH2rfDz6EGx",  # Pro plan
            "price_1SQ3i2IDKuDXFSH2ZVtCqL2f",  # Enterprise plan
        ]

        results = []
        all_valid = True

        for price_id in price_ids:
            try:
                price = stripe.Price.retrieve(price_id)
                product = stripe.Product.retrieve(price.product)

                status = "✓ Valid" if price.active else "⚠ Inactive"
                results.append(
                    f"{status}: {price_id} - {product.name} "
                    f"({price.unit_amount/100:.2f} {price.currency.upper()}"
                    f"/{price.recurring.interval if price.recurring else 'once'})"
                )
            except stripe.error.InvalidRequestError:
                results.append(f"✗ Invalid: {price_id} - Not found in Stripe account")
                all_valid = False
            except Exception as e:
                results.append(f"✗ Error checking {price_id}: {str(e)}")
                all_valid = False

        if all_valid:
            return True, "All configured price IDs are valid", results
        else:
            return False, "Some price IDs are invalid or not found", results
    except Exception as e:
        return False, f"Error verifying price IDs: {str(e)}", []

async def check_webhook_endpoint() -> Tuple[bool, str, List[str]]:
    """Check configured webhook endpoints."""
    try:
        stripe.api_key = SETTINGS.STRIPE_API_KEY

        # List webhook endpoints
        endpoints = stripe.WebhookEndpoint.list(limit=10)

        if not endpoints.data:
            return False, "No webhook endpoints configured", []

        endpoint_info = []
        for endpoint in endpoints.data:
            status = "✓ Enabled" if endpoint.status == "enabled" else "✗ Disabled"
            endpoint_info.append(
                f"{status}: {endpoint.url}\n"
                f"     Events: {', '.join(endpoint.enabled_events[:5])}"
                f"{' (+' + str(len(endpoint.enabled_events) - 5) + ' more)' if len(endpoint.enabled_events) > 5 else ''}"
            )

        return True, f"Found {len(endpoints.data)} webhook endpoint(s)", endpoint_info
    except Exception as e:
        return False, f"Error checking webhooks: {str(e)}", []

async def check_configuration_values():
    """Check all Stripe-related configuration values."""
    print_info("Checking configuration values...")

    config_items = [
        ("STRIPE_API_KEY", "***" + SETTINGS.STRIPE_API_KEY[-4:] if len(SETTINGS.STRIPE_API_KEY) > 4 else "Not set", bool(SETTINGS.STRIPE_API_KEY)),
        ("STRIPE_WEBHOOK_SECRET", "***" + SETTINGS.STRIPE_WEBHOOK_SECRET[-4:] if len(SETTINGS.STRIPE_WEBHOOK_SECRET) > 4 else "Not set", bool(SETTINGS.STRIPE_WEBHOOK_SECRET)),
        ("STRIPE_SUCCESS_URL", SETTINGS.STRIPE_SUCCESS_URL, True),
        ("STRIPE_CANCEL_URL", SETTINGS.STRIPE_CANCEL_URL, True),
        ("STRIPE_PORTAL_RETURN_URL", SETTINGS.STRIPE_PORTAL_RETURN_URL, True),
    ]

    for name, value, is_set in config_items:
        if is_set:
            print_success(f"{name}: {value}")
        else:
            print_error(f"{name}: Not set")

async def run_diagnostics():
    """Run all diagnostic checks."""
    print_header("Stripe Configuration Troubleshooting")

    print_info(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Stripe Python SDK version: {stripe.__version__}\n")

    # Configuration check
    print_header("1. Configuration Check")
    await check_configuration_values()

    # API Key Format Check
    print_header("2. API Key Format Check")
    success, message = check_api_key_format()
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Fix: Set STRIPE_API_KEY in your .env file with a valid secret key from Stripe Dashboard")
        print_info("Get your API keys from: https://dashboard.stripe.com/apikeys")
        return  # Stop here if API key is invalid

    # Webhook Secret Check
    print_header("3. Webhook Secret Check")
    success, message = check_webhook_secret_format()
    if success:
        print_success(message)
    else:
        print_warning(message)
        print_info("Fix: Set STRIPE_WEBHOOK_SECRET in your .env file")
        print_info("Get your webhook secret from: https://dashboard.stripe.com/webhooks")

    # API Connectivity Test
    print_header("4. API Connectivity Test")
    success, message = await test_api_connectivity()
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Troubleshooting tips:")
        print_info("  - Verify your API key is correct and active")
        print_info("  - Check your internet connection")
        print_info("  - Verify no firewall is blocking Stripe API (api.stripe.com)")
        return  # Stop here if we can't connect

    # Products and Prices Check
    print_header("5. Products and Prices Check")
    success, message, price_info = await check_products_and_prices()
    if success:
        print_success(message)
        for info in price_info:
            amount_display = f"{info['amount']/100:.2f}" if info['amount'] else "0.00"
            print(f"  - {info['product_name']}")
            print(f"    Price ID: {info['price_id']}")
            print(f"    Amount: {amount_display} {info['currency'].upper()}/{info['interval']}")
    else:
        print_warning(message)
        print_info("You may need to create products and prices in Stripe Dashboard")
        print_info("Visit: https://dashboard.stripe.com/products")

    # Verify Configured Price IDs
    print_header("6. Verify Application Price IDs")
    success, message, results = await verify_price_ids()
    if success:
        print_success(message)
    else:
        print_error(message)

    for result in results:
        if "✓" in result:
            print(f"  {Colors.GREEN}{result}{Colors.END}")
        elif "⚠" in result:
            print(f"  {Colors.YELLOW}{result}{Colors.END}")
        else:
            print(f"  {Colors.RED}{result}{Colors.END}")

    if not success:
        print_info("\nFix: Update the price IDs in back/api/views/billing_view.py with your actual Stripe price IDs")

    # Test Customer Creation
    print_header("7. Customer Creation Test")
    success, message = await test_customer_creation()
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Check API key permissions and Stripe account status")

    # Webhook Configuration Check
    print_header("8. Webhook Configuration Check")
    success, message, endpoints = await check_webhook_endpoint()
    if success:
        print_success(message)
        for endpoint in endpoints:
            print(f"  {endpoint}")
    else:
        print_warning(message)
        print_info("\nWebhook setup instructions:")
        print_info("  1. Go to: https://dashboard.stripe.com/webhooks")
        print_info("  2. Click 'Add endpoint'")
        print_info("  3. Use URL: https://your-domain.com/api/webhooks/stripe")
        print_info("  4. Select events: checkout.session.completed, customer.subscription.*")
        print_info("  5. Copy the webhook signing secret to STRIPE_WEBHOOK_SECRET")

    # Summary
    print_header("Summary and Recommendations")

    print_info("Configuration URLs:")
    print(f"  Success URL: {SETTINGS.STRIPE_SUCCESS_URL}")
    print(f"  Cancel URL: {SETTINGS.STRIPE_CANCEL_URL}")
    print(f"  Portal Return URL: {SETTINGS.STRIPE_PORTAL_RETURN_URL}")

    print_info("\nMake sure these URLs match your actual application URLs!")

    print_info("\nFor more help:")
    print_info("  - Stripe Dashboard: https://dashboard.stripe.com")
    print_info("  - Stripe Logs: https://dashboard.stripe.com/logs")
    print_info("  - Stripe Documentation: https://stripe.com/docs/api")

    print(f"\n{Colors.BOLD}{Colors.GREEN}Diagnostics completed!{Colors.END}\n")

async def main():
    """Main entry point."""
    try:
        await run_diagnostics()
    except KeyboardInterrupt:
        print_warning("\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
