"""convert_is_active_to_boolean

Revision ID: 7c6d5e4f3a2b
Revises: 8b7c6d5e4f3a
Create Date: 2025-06-09 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c6d5e4f3a2b'
down_revision = '8b7c6d5e4f3a'
branch_labels = None
depends_on = None


def upgrade():
    # The companies table already has is_active as boolean, so no need to convert it
    
    # Add is_active column to job_offers table as boolean
    op.add_column('job_offers', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.execute("UPDATE job_offers SET is_active = true WHERE is_active IS NULL")


def downgrade():
    # Remove is_active column from job_offers table
    op.drop_column('job_offers', 'is_active')
