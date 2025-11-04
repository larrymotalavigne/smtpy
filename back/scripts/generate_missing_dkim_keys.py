"""
Script to generate DKIM keys for existing domains that don't have them.
This fixes the issue where domains created before the DKIM feature show placeholder values.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shared.models.domain import Domain
from api.services.dkim_service import DKIMService


async def main():
    """Generate DKIM keys for domains that don't have them."""

    # Get database URL from environment or use default
    import os
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg://smtpy:smtpy@localhost:5432/smtpy")

    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("🔑 Generating DKIM keys for existing domains...")

    async with async_session() as session:
        # Get all domains without DKIM keys
        stmt = select(Domain).where(
            (Domain.dkim_public_key == None) | (Domain.dkim_public_key == "")
        )
        result = await session.execute(stmt)
        domains_without_keys = result.scalars().all()

        if not domains_without_keys:
            print("✅ All domains already have DKIM keys!")
            return

        print(f"Found {len(domains_without_keys)} domains without DKIM keys:")
        for domain in domains_without_keys:
            print(f"  - {domain.name} (ID: {domain.id})")

        print("\nGenerating DKIM keys...")
        dkim_service = DKIMService()

        for domain in domains_without_keys:
            print(f"\nProcessing {domain.name}...")

            # Generate DKIM keys
            private_key, public_key = dkim_service.generate_dkim_keypair()
            selector = dkim_service.get_dkim_selector()

            # Update domain with DKIM keys
            domain.dkim_public_key = public_key
            domain.dkim_private_key = private_key
            domain.dkim_selector = selector

            print(f"  ✓ Generated keys with selector: {selector}")
            print(f"  ✓ Public key: {public_key[:50]}...")

        # Commit all changes
        await session.commit()

        print(f"\n✅ Successfully generated DKIM keys for {len(domains_without_keys)} domains!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
