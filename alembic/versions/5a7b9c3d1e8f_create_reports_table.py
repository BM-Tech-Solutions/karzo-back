"""create reports table

Revision ID: 5a7b9c3d1e8f
Revises: 4f5dc2e1be72
Create Date: 2025-05-28 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '5a7b9c3d1e8f'
down_revision = '4f5dc2e1be72'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interview_id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('duration', sa.String(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('strengths', JSON(), nullable=True),
        sa.Column('improvements', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ),
        sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_reports_id'), table_name='reports')
    op.drop_table('reports')
