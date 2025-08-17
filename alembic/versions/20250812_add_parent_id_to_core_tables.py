"""Add parent_id to companies, guest_candidates, and job_offers

Revision ID: 20250812_add_parent_id
Revises: 20250812_merge_heads
Create Date: 2025-08-12 11:06:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250812_add_parent_id'
down_revision: Union[str, None] = '20250812_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # companies.parent_id
    op.add_column('companies', sa.Column('parent_id', sa.Integer(), nullable=True))

    # guest_candidates.parent_id
    op.add_column('guest_candidates', sa.Column('parent_id', sa.Integer(), nullable=True))

    # job_offers.parent_id
    op.add_column('job_offers', sa.Column('parent_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # job_offers.parent_id
    op.drop_column('job_offers', 'parent_id')

    # guest_candidates.parent_id
    op.drop_column('guest_candidates', 'parent_id')

    # companies.parent_id
    op.drop_column('companies', 'parent_id')
