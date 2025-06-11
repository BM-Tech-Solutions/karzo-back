"""Add error_message to guest_reports

Revision ID: 202506111155
Revises: 202506111132
Create Date: 2025-06-11 11:55:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202506111155'
down_revision = '202506111132'  # Previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Add error_message column to guest_reports table
    op.add_column('guest_reports', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('guest_reports', 'error_message')
