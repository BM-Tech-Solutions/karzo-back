"""consolidated_schema

Revision ID: 0572051273b2
Revises: 202506111155
Create Date: 2025-06-12 13:30:02.384120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0572051273b2'
down_revision: Union[str, None] = None  # Set to None to make this the starting migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables in a single migration."""
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    # Users table
    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False, unique=True),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('role', sa.String(length=50), nullable=True),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('resume_url', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Companies table
    if 'companies' not in tables:
        op.create_table(
            'companies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False, unique=True),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('size', sa.String(length=50), nullable=True),
            sa.Column('sector', sa.String(length=100), nullable=True),
            sa.Column('about', sa.Text(), nullable=True),
            sa.Column('website', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Job offers table
    if 'job_offers' not in tables:
        op.create_table(
            'job_offers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Job requirements table
    if 'job_requirements' not in tables:
        op.create_table(
            'job_requirements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('requirement', sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Job questions table
    if 'job_questions' not in tables:
        op.create_table(
            'job_questions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('question', sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Invitations table
    if 'invitations' not in tables:
        op.create_table(
            'invitations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('token', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Applications table
    if 'applications' not in tables:
        op.create_table(
            'applications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Interviews table
    if 'interviews' not in tables:
        op.create_table(
            'interviews',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('conversation_id', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('report_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Reports table
    if 'reports' not in tables:
        op.create_table(
            'reports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('interview_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.JSON(), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('strengths', sa.ARRAY(sa.String()), nullable=True),
            sa.Column('weaknesses', sa.ARRAY(sa.String()), nullable=True),
            sa.Column('recommendation', sa.Text(), nullable=True),
            sa.Column('score', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Guest candidates table
    if 'guest_candidates' not in tables:
        op.create_table(
            'guest_candidates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Guest interviews table
    if 'guest_interviews' not in tables:
        op.create_table(
            'guest_interviews',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('guest_candidate_id', sa.Integer(), nullable=False),
            sa.Column('conversation_id', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['guest_candidate_id'], ['guest_candidates.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Guest reports table
    if 'guest_reports' not in tables:
        op.create_table(
            'guest_reports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('guest_interview_id', sa.Integer(), nullable=False),
            sa.Column('candidate_email', sa.String(length=255), nullable=False),
            sa.Column('conversation_id', sa.String(length=255), nullable=True),
            sa.Column('transcript', sa.JSON(), nullable=True),
            sa.Column('transcript_summary', sa.Text(), nullable=True),
            sa.Column('feedback', sa.Text(), nullable=True),
            sa.Column('strengths', sa.ARRAY(sa.String()), nullable=True),
            sa.Column('improvements', sa.ARRAY(sa.String()), nullable=True),
            sa.Column('score', sa.Integer(), nullable=True),
            sa.Column('duration', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['guest_interview_id'], ['guest_interviews.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    # Drop tables in reverse order of creation
    if 'guest_reports' in tables:
        op.drop_table('guest_reports')
    if 'guest_interviews' in tables:
        op.drop_table('guest_interviews')
    if 'guest_candidates' in tables:
        op.drop_table('guest_candidates')
    if 'reports' in tables:
        op.drop_table('reports')
    if 'interviews' in tables:
        op.drop_table('interviews')
    if 'applications' in tables:
        op.drop_table('applications')
    if 'invitations' in tables:
        op.drop_table('invitations')
    if 'job_questions' in tables:
        op.drop_table('job_questions')
    if 'job_requirements' in tables:
        op.drop_table('job_requirements')
    if 'job_offers' in tables:
        op.drop_table('job_offers')
    if 'companies' in tables:
        op.drop_table('companies')
    if 'users' in tables:
        op.drop_table('users')
