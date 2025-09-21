"""Add more_technical field to invitations table

Revision ID: 20250921_add_more_technical
Revises: 20250913_pwd_resets, 876f1d9afc00
Create Date: 2025-09-21 09:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250921_add_more_technical'
down_revision: Union[str, Sequence[str], None] = ('20250913_pwd_resets', '876f1d9afc00')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add more_technical field to invitations table."""
    # Add the more_technical column to invitations table
    op.add_column('invitations', sa.Column('more_technical', sa.Boolean(), nullable=True, default=False))


def downgrade() -> None:
    """Remove more_technical field from invitations table."""
    # Remove the more_technical column from invitations table
    op.drop_column('invitations', 'more_technical')
