#!/usr/bin/env python3
"""
Seed development database with test data for E2E tests.

This script creates:
- Admin user (username: admin, password: password)
- Test organization
- Test domain
- Sample data for testing
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from shared.core.db import get_async_session
from shared.models import User, UserRole, Organization, Domain


async def seed_database():
    """Seed the database with test data."""
    print("🌱 Seeding development database...")

    # get_async_session is a generator, not a context manager
    async for session in get_async_session():
        # Check if admin user already exists
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("ℹ️  Admin user already exists, skipping seed")
            break

        # Create test organization
        print("Creating test organization...")
        org = Organization(
            name="Test Organization",
            email="org@test.com"
        )
        session.add(org)
        await session.flush()  # Get the org ID

        # Create admin user
        print("Creating admin user (username: admin, password: password)...")
        admin_user = User(
            username="admin",
            email="admin@test.com",
            is_active=True,
            is_verified=True,
            role=UserRole.ADMIN,
            organization_id=org.id
        )
        admin_user.set_password("password")
        session.add(admin_user)

        # Create test user
        print("Creating test user (username: testuser, password: testpass)...")
        test_user = User(
            username="testuser",
            email="testuser@test.com",
            is_active=True,
            is_verified=True,
            role=UserRole.USER,
            organization_id=org.id
        )
        test_user.set_password("testpass")
        session.add(test_user)

        # Create test domain
        print("Creating test domain (test.example.com)...")
        test_domain = Domain(
            name="test.example.com",
            organization_id=org.id
        )
        session.add(test_domain)

        # Commit all changes
        await session.commit()

        print("✅ Database seeded successfully!")
        print("\n📝 Test Credentials:")
        print("   Admin: username=admin, password=password")
        print("   User:  username=testuser, password=testpass")
        print("\n🏢 Test Organization: Test Organization")
        print("🌐 Test Domain: test.example.com")

        # Break after first session
        break


async def main():
    """Main entry point."""
    try:
        await seed_database()
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
