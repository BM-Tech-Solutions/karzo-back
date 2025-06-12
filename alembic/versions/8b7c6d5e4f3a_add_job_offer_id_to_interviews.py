"""add_job_offer_id_to_interviews

Revision ID: 8b7c6d5e4f3a
Revises: 9a8b7c6d5e4f
Create Date: 2025-06-09 13:56:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b7c6d5e4f3a'
down_revision = '9a8b7c6d5e4f'
branch_labels = None
depends_on = None


def upgrade():
    # Add job_offer_id column to interviews table
    op.add_column('interviews', sa.Column('job_offer_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_interviews_job_offer_id', 
        'interviews', 'job_offers', 
        ['job_offer_id'], ['id']
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_interviews_job_offer_id', 'interviews', type_='foreignkey')
    
    # Drop job_offer_id column
    op.drop_column('interviews', 'job_offer_id')
