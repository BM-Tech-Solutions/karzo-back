"""add_candidate_summary_columns

Revision ID: 20250618_add_candidate_summary
Revises: 0572051273b2
Create Date: 2025-06-18 13:29:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250618_add_candidate_summary'
down_revision: Union[str, None] = '0572051273b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add candidate_summary column to guest_candidates and guest_interviews tables."""
    # Add candidate_summary column to guest_candidates table
    op.add_column('guest_candidates', sa.Column('candidate_summary', sa.Text(), nullable=True))
    
    # Add candidate_summary column to guest_interviews table
    op.add_column('guest_interviews', sa.Column('candidate_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove candidate_summary column from guest_candidates and guest_interviews tables."""
    # Remove candidate_summary column from guest_interviews table
    op.drop_column('guest_interviews', 'candidate_summary')
    
    # Remove candidate_summary column from guest_candidates table
    op.drop_column('guest_candidates', 'candidate_summary')
