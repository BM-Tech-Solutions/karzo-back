"""Add guest reports table

Revision ID: 202506111132
Revises: 202506110855
Create Date: 2025-06-11 11:32:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '202506111132'
down_revision = '202506110855'  # Previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Create guest_reports table
    op.create_table(
        'guest_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guest_interview_id', sa.Integer(), nullable=False),
        sa.Column('candidate_email', sa.String(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('duration', sa.String(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('strengths', JSON(), nullable=True),
        sa.Column('improvements', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('status', sa.String(), nullable=False, server_default='processing'),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('transcript', JSON(), nullable=True),
        sa.Column('transcript_summary', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['guest_interview_id'], ['guest_interviews.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guest_reports_id'), 'guest_reports', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_guest_reports_id'), table_name='guest_reports')
    op.drop_table('guest_reports')
