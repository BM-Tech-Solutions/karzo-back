"""Add language_level field to guest_reports table

Revision ID: 20250909_language_level
Revises: 876f1d9afc00
Create Date: 2025-09-09 09:41:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250909_language_level'
down_revision: Union[str, None] = '20250812_add_parent_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add language_level field to guest_reports table."""
    # Add the language_level column to guest_reports table
    op.add_column('guest_reports', sa.Column('language_level', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove language_level field from guest_reports table."""
    # Remove the language_level column from guest_reports table
    op.drop_column('guest_reports', 'language_level')
