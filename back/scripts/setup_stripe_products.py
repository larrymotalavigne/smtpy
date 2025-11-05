#!/usr/bin/env python3
"""
Setup Stripe products and prices for SMTPy.
Run this script to create the necessary products in your Stripe account.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import stripe
from shared.core.config import SETTINGS

# Initialize Stripe
stripe.api_key = SETTINGS.STRIPE_API_KEY


def create_products_and_prices():
    """Create Stripe products and prices for SMTPy plans."""

    print("🎯 Setting up Stripe products and prices...")
    print(f"Using API key: {stripe.api_key[:20]}...")

    products_to_create = [
        {
            "name": "SMTPy Pro",
            "description": "Plan Pro - Pour les professionnels et petites équipes",
            "price_data": {
                "nickname": "Pro Monthly",
                "amount": 900,  # 9.00 EUR
                "currency": "eur",
                "recurring": {"interval": "month"},
            },
            "metadata": {
                "plan_id": "pro",
                "domains": "5",
                "aliases": "-1",  # unlimited
                "emails_per_month": "10000"
            }
        },
        {
            "name": "SMTPy Entreprise",
            "description": "Plan Entreprise - Solution sur mesure pour les grandes organisations",
            "price_data": {
                "nickname": "Entreprise Monthly",
                "amount": 0,  # Custom pricing
                "currency": "eur",
                "recurring": {"interval": "month"},
            },
            "metadata": {
                "plan_id": "entreprise",
                "domains": "-1",  # unlimited
                "aliases": "-1",  # unlimited
                "emails_per_month": "-1"  # unlimited
            }
        }
    ]

    created_products = []

    for product_data in products_to_create:
        try:
            # Create product
            print(f"\n📦 Creating product: {product_data['name']}")
            product = stripe.Product.create(
                name=product_data["name"],
                description=product_data["description"],
                metadata=product_data["metadata"]
            )
            print(f"   ✅ Product created: {product.id}")

            # Create price
            print(f"💰 Creating price for {product_data['name']}")
            price = stripe.Price.create(
                product=product.id,
                unit_amount=product_data["price_data"]["amount"],
                currency=product_data["price_data"]["currency"],
                recurring=product_data["price_data"]["recurring"],
                nickname=product_data["price_data"]["nickname"]
            )
            print(f"   ✅ Price created: {price.id}")

            created_products.append({
                "product_id": product.id,
                "price_id": price.id,
                "name": product_data["name"],
                "plan_id": product_data["metadata"]["plan_id"]
            })

        except stripe.error.StripeError as e:
            print(f"   ❌ Error creating {product_data['name']}: {str(e)}")

    print("\n" + "="*60)
    print("✅ Setup Complete! Here are your Stripe IDs:")
    print("="*60)

    for item in created_products:
        print(f"\n{item['name']}:")
        print(f"  Product ID: {item['product_id']}")
        print(f"  Price ID:   {item['price_id']}")
        print(f"  Plan ID:    {item['plan_id']}")

    print("\n" + "="*60)
    print("📝 Update your billing_view.py with these price IDs:")
    print("="*60)

    for item in created_products:
        print(f"  '{item['plan_id']}' -> '{item['price_id']}'")

    print("\n✨ You can now test Stripe checkout!")
    print("🔗 View in Stripe Dashboard: https://dashboard.stripe.com/test/products")


if __name__ == "__main__":
    if not SETTINGS.STRIPE_API_KEY or SETTINGS.STRIPE_API_KEY == "":
        print("❌ Error: STRIPE_API_KEY not set in environment")
        print("Please set STRIPE_API_KEY in your .env file")
        sys.exit(1)

    if not SETTINGS.STRIPE_API_KEY.startswith("sk_test_"):
        response = input("⚠️  Warning: Not using a test key. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    create_products_and_prices()
