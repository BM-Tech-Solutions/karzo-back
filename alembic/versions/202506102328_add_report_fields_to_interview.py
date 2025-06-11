"""Add report fields to Interview model

Revision ID: 202506102328
Revises: 202506101622
Create Date: 2025-06-10 23:28:18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202506102328'
down_revision = '202506101622'  # Previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to the interviews table
    op.add_column('interviews', sa.Column('conversation_id', sa.String(), nullable=True))
    op.add_column('interviews', sa.Column('report_id', sa.String(), nullable=True))
    op.add_column('interviews', sa.Column('report_status', sa.String(), nullable=True))
    op.add_column('interviews', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')))


def downgrade():
    # Remove columns from the interviews table
    op.drop_column('interviews', 'conversation_id')
    op.drop_column('interviews', 'report_id')
    op.drop_column('interviews', 'report_status')
    op.drop_column('interviews', 'created_at')
