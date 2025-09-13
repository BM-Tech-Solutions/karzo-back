"""add company_password_resets table

Revision ID: 20250913_add_company_password_resets
Revises: 20250909_add_language_level_to_guest_reports
Create Date: 2025-09-13
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20250913_pwd_resets'
down_revision = '20250909_language_level'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'company_password_resets',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    # Alembic's create_table doesn't accept index=True directly for some backends
    op.create_index('ix_company_password_resets_email', 'company_password_resets', ['email'])


def downgrade() -> None:
    op.drop_index('ix_company_password_resets_email', table_name='company_password_resets')
    op.drop_table('company_password_resets')
