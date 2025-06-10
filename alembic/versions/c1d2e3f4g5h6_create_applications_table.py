"""create applications table

Revision ID: c1d2e3f4g5h6
Revises: b1c2d3e4f5g6_add_missing_invitation_columns
Create Date: 2025-06-10 11:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = 'b1c2d3e4f5g6'
branch_labels = None
depends_on = None


def upgrade():
    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('resume_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('job_offer_id', sa.Integer(), nullable=True),
        sa.Column('invitation_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ),
        sa.ForeignKeyConstraint(['invitation_id'], ['invitations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
    op.create_index(op.f('ix_applications_email'), 'applications', ['email'], unique=False)


def downgrade():
    # Drop applications table
    op.drop_index(op.f('ix_applications_email'), table_name='applications')
    op.drop_index(op.f('ix_applications_id'), table_name='applications')
    op.drop_table('applications')
