"""merge multiple heads

Revision ID: 6d39478753c0
Revises: 004, 005_remove_forwarded_to
Create Date: 2025-11-06 16:23:10.431338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d39478753c0'
down_revision: Union[str, Sequence[str], None] = ('004', '005_remove_forwarded_to')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
