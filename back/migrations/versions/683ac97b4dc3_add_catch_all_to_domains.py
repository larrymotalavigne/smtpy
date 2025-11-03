"""add_catch_all_to_domains

Revision ID: 683ac97b4dc3
Revises: 003
Create Date: 2025-11-03 08:24:19.559409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '683ac97b4dc3'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add catch_all column to domains table
    op.add_column('domains', sa.Column('catch_all', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove catch_all column from domains table
    op.drop_column('domains', 'catch_all')
