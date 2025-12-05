"""remove forwarded_to column from messages

Revision ID: 005_remove_forwarded_to
Revises: 8e5a401deec3
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_remove_forwarded_to'
down_revision = '8e5a401deec3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove forwarded_to column from messages table."""
    op.drop_column('messages', 'forwarded_to')


def downgrade() -> None:
    """Add back forwarded_to column to messages table."""
    op.add_column('messages',
        sa.Column('forwarded_to', sa.String(length=320), nullable=True)
    )
