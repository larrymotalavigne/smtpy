"""add_dkim_keys_to_domains

Revision ID: 8e5a401deec3
Revises: 683ac97b4dc3
Create Date: 2025-11-03 17:33:10.897419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e5a401deec3'
down_revision: Union[str, None] = '683ac97b4dc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add DKIM private key column
    op.add_column('domains', sa.Column('dkim_private_key', sa.Text(), nullable=True))

    # Add DKIM selector column with default value
    op.add_column('domains', sa.Column('dkim_selector', sa.String(length=63), nullable=True, server_default='default'))


def downgrade() -> None:
    # Remove DKIM columns
    op.drop_column('domains', 'dkim_selector')
    op.drop_column('domains', 'dkim_private_key')
