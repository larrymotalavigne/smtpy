"""No-op migration to validate Alembic env and versioning

Revision ID: 002
Revises: 001
Create Date: 2025-10-16 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op  # noqa: F401  (kept for consistency)
import sqlalchemy as sa  # noqa: F401  (kept for consistency)

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Intentionally empty: this is a no-op migration to ensure Alembic works end-to-end
    pass


def downgrade() -> None:
    # Intentionally empty: this migration does not change schema
    pass
