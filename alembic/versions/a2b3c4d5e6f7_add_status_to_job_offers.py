"""Add status field to job_offers table

Revision ID: a2b3c4d5e6f7
Revises: 
Create Date: 2025-06-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = '7c6d5e4f3a2b'  # Points to the current head migration
branch_labels = None
depends_on = None

def upgrade():
    # Add status column with default value 'active'
    op.add_column('job_offers', sa.Column('status', sa.String(), server_default='active'))

def downgrade():
    # Remove status column
    op.drop_column('job_offers', 'status')
