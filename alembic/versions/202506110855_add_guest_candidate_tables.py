"""Add guest candidate tables

Revision ID: 202506110855
Revises: 202506102328
Create Date: 2025-06-11 08:55:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202506110855'
down_revision = '202506102328'  # Previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Create guest_candidates table
    op.create_table(
        'guest_candidates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('resume_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guest_candidates_email'), 'guest_candidates', ['email'], unique=True)
    op.create_index(op.f('ix_guest_candidates_id'), 'guest_candidates', ['id'], unique=False)
    
    # Create guest_interviews table
    op.create_table(
        'guest_interviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guest_candidate_id', sa.Integer(), nullable=True),
        sa.Column('job_offer_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('report_id', sa.String(), nullable=True),
        sa.Column('report_status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['guest_candidate_id'], ['guest_candidates.id'], ),
        sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guest_interviews_id'), 'guest_interviews', ['id'], unique=False)
    
    # Add guest_candidate_id to applications table
    op.add_column('applications', sa.Column('guest_candidate_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'applications', 'guest_candidates', ['guest_candidate_id'], ['id'])


def downgrade():
    # Remove guest_candidate_id from applications table
    op.drop_constraint(None, 'applications', type_='foreignkey')
    op.drop_column('applications', 'guest_candidate_id')
    
    # Drop guest_interviews table
    op.drop_index(op.f('ix_guest_interviews_id'), table_name='guest_interviews')
    op.drop_table('guest_interviews')
    
    # Drop guest_candidates table
    op.drop_index(op.f('ix_guest_candidates_id'), table_name='guest_candidates')
    op.drop_index(op.f('ix_guest_candidates_email'), table_name='guest_candidates')
    op.drop_table('guest_candidates')
