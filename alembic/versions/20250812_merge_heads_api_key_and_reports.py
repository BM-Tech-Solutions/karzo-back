"""Merge heads: api_key and report_content branches

Revision ID: 20250812_merge_heads
Revises: 876f1d9afc00, 20250812_add_api_key
Create Date: 2025-08-12 10:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250812_merge_heads'
down_revision = ('876f1d9afc00', '20250812_add_api_key')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """This is a merge migration; no schema changes required."""
    pass


def downgrade() -> None:
    """No-op for merge downgrade."""
    pass
