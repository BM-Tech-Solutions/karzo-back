"""add_candidate_id_to_interviews

Revision ID: a1b2c3d4e5f6
Revises: c1d2e3f4g5h6
Create Date: 2025-06-10 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c1d2e3f4g5h6'  # Update this to match your last migration
branch_labels = None
depends_on = None


def upgrade():
    # Add candidate_id column to interviews table
    op.add_column('interviews', sa.Column('candidate_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_interviews_candidate_id_users',
        'interviews', 'users',
        ['candidate_id'], ['id']
    )


def downgrade():
    # Remove candidate_id column from interviews table
    op.drop_constraint('fk_interviews_candidate_id_users', 'interviews', type_='foreignkey')
    op.drop_column('interviews', 'candidate_id')
