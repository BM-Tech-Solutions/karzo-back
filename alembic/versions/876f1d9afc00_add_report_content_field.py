"""Add report_content field to guest_reports table

Revision ID: 876f1d9afc00
Revises: 20250204_add_tts_parameters
Create Date: 2025-08-05 13:40:43.384431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '876f1d9afc00'
down_revision: Union[str, None] = '20250204_add_tts_parameters'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add report_content field to guest_reports table."""
    # Add the report_content column to guest_reports table
    op.add_column('guest_reports', sa.Column('report_content', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove report_content field from guest_reports table."""
    # Remove the report_content column from guest_reports table
    op.drop_column('guest_reports', 'report_content')
