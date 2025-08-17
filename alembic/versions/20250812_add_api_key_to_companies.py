"""
add api_key column to companies

Revision ID: 20250812_add_api_key
Revises: 20250618_add_candidate_summary
Create Date: 2025-08-12 10:45:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250812_add_api_key'
down_revision = '20250618_add_candidate_summary'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('companies', sa.Column('api_key', sa.String(), nullable=True))
    op.create_index('ix_companies_api_key', 'companies', ['api_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_companies_api_key', table_name='companies')
    op.drop_column('companies', 'api_key')
