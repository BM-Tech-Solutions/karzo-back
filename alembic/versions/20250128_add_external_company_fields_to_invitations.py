"""Add external company fields to invitations

Revision ID: 20250128_add_external_company_fields
Revises: 20250618_add_candidate_summary
Create Date: 2025-01-28 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250128_external_company'
down_revision = '20250618_add_candidate_summary'
branch_labels = None
depends_on = None


def upgrade():
    # Add external company fields to invitations table
    op.add_column('invitations', sa.Column('external_company_name', sa.String(), nullable=True))
    op.add_column('invitations', sa.Column('external_company_email', sa.String(), nullable=True))
    op.add_column('invitations', sa.Column('external_company_size', sa.String(), nullable=True))
    op.add_column('invitations', sa.Column('external_company_sector', sa.String(), nullable=True))
    op.add_column('invitations', sa.Column('external_company_about', sa.Text(), nullable=True))
    op.add_column('invitations', sa.Column('external_company_website', sa.String(), nullable=True))


def downgrade():
    # Remove external company fields from invitations table
    op.drop_column('invitations', 'external_company_website')
    op.drop_column('invitations', 'external_company_about')
    op.drop_column('invitations', 'external_company_sector')
    op.drop_column('invitations', 'external_company_size')
    op.drop_column('invitations', 'external_company_email')
    op.drop_column('invitations', 'external_company_name')
