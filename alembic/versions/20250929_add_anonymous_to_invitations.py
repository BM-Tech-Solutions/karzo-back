"""
Add anonymous column to invitations

Revision ID: 20250929_add_anonymous
Revises: 20250921_add_more_technical
Create Date: 2025-09-29 09:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250929_add_anonymous'
down_revision = '20250921_add_more_technical'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('invitations', sa.Column('anonymous', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('invitations', 'anonymous')
