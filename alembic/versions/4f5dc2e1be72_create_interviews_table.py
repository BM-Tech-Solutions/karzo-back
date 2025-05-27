"""create interviews table

Revision ID: 4f5dc2e1be72
Revises: 2a8b3c4d5e6f
Create Date: 2025-05-26 16:14:12.812223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f5dc2e1be72'
down_revision: Union[str, None] = '2a8b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('interviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interviews_id'), 'interviews', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_interviews_id'), table_name='interviews')
    op.drop_table('interviews')
