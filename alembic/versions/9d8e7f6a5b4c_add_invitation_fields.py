"""Add new fields to invitation model

Revision ID: 9d8e7f6a5b4c
Revises: a2b3c4d5e6f7
Create Date: 2025-06-10 09:39:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d8e7f6a5b4c'
down_revision = 'a2b3c4d5e6f7'  # Points to add_status_to_job_offers
branch_labels = None
depends_on = None


def upgrade():
    # Create the invitations table first
    op.create_table(
        'invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('candidate_email', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('job_offer_id', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('resend_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], name='fk_invitations_job_offer_id'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on token for faster lookups
    op.create_index('ix_invitations_token', 'invitations', ['token'], unique=True)
    
    # Create index on candidate_email for faster lookups
    op.create_index('ix_invitations_candidate_email', 'invitations', ['candidate_email'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index('ix_invitations_candidate_email', table_name='invitations')
    op.drop_index('ix_invitations_token', table_name='invitations')
    
    # Drop the entire invitations table
    op.drop_table('invitations')
