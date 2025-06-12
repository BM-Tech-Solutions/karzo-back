"""add_job_id_to_job_requirements

Revision ID: 9a8b7c6d5e4f
Revises: ba0df5459d95
Create Date: 2025-06-09 13:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a8b7c6d5e4f'
down_revision = 'ba0df5459d95'
branch_labels = None
depends_on = None


def upgrade():
    # Add job_id column to job_requirements table
    op.add_column('job_requirements', sa.Column('job_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_job_requirements_job_id', 
        'job_requirements', 'jobs', 
        ['job_id'], ['id'], 
        ondelete='CASCADE'
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_job_requirements_job_id', 'job_requirements', type_='foreignkey')
    
    # Drop job_id column
    op.drop_column('job_requirements', 'job_id')
