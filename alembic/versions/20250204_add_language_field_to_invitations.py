"""Add language field to invitations

Revision ID: 20250204_add_language_field
Revises: 20250618_add_candidate_summary
Create Date: 2025-02-04 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250204_add_language_field'
down_revision = '20250128_external_company'
branch_labels = None
depends_on = None


def upgrade():
    # Add language column to invitations table
    op.add_column('invitations', sa.Column('language', sa.String(), nullable=True))


def downgrade():
    # Remove language column from invitations table
    op.drop_column('invitations', 'language')
