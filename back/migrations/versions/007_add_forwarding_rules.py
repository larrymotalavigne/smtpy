"""Add forwarding rules table

Revision ID: 007
Revises: 006
Create Date: 2025-12-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create forwarding_rules table
    op.create_table('forwarding_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alias_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('condition_type', sa.Enum(
            'SENDER_CONTAINS', 'SENDER_EQUALS', 'SENDER_DOMAIN',
            'SUBJECT_CONTAINS', 'SUBJECT_EQUALS',
            'SIZE_GREATER_THAN', 'SIZE_LESS_THAN', 'HAS_ATTACHMENTS',
            name='ruleconditiontype'
        ), nullable=False),
        sa.Column('condition_value', sa.Text(), nullable=False),
        sa.Column('action_type', sa.Enum(
            'FORWARD', 'BLOCK', 'REDIRECT',
            name='ruleactiontype'
        ), nullable=False),
        sa.Column('action_value', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('match_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['alias_id'], ['aliases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forwarding_rules_alias_id'), 'forwarding_rules', ['alias_id'], unique=False)


def downgrade() -> None:
    # Drop forwarding_rules table
    op.drop_index(op.f('ix_forwarding_rules_alias_id'), table_name='forwarding_rules')
    op.drop_table('forwarding_rules')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS ruleconditiontype')
    op.execute('DROP TYPE IF EXISTS ruleactiontype')
