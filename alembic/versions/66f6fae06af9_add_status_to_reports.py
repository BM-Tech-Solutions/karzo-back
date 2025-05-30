"""add_status_to_reports

Revision ID: 66f6fae06af9
Revises: 5a7b9c3d1e8f
Create Date: 2025-05-30 21:05:50.265328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66f6fae06af9'
down_revision: Union[str, None] = '5a7b9c3d1e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add status column with default value 'processing'
    op.add_column('reports', sa.Column('status', sa.String(), nullable=False, server_default='processing'))
    op.add_column('reports', sa.Column('conversation_id', sa.String(), nullable=True))
    op.add_column('reports', sa.Column('transcript', sa.JSON(), nullable=True))
    op.add_column('reports', sa.Column('transcript_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reports', 'status')
    op.drop_column('reports', 'conversation_id')
    op.drop_column('reports', 'transcript')
    op.drop_column('reports', 'transcript_summary')


