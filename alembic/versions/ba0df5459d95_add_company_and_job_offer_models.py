"""Add company and job offer models

Revision ID: ba0df5459d95
Revises: 66f6fae06af9
Create Date: 2025-06-09 12:23:20.768760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba0df5459d95'
down_revision: Union[str, None] = '66f6fae06af9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy.engine.reflection import Inspector
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    # Create companies table if it doesn't exist
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
    
    # Create job_offers table if it doesn't exist
    if 'job_offers' not in tables:
        op.create_table(
            'job_offers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create job_requirements table for job offers if it doesn't exist
    if 'job_requirements' not in tables:
        op.create_table(
            'job_requirements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('requirement', sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create job_questions table if it doesn't exist
    if 'job_questions' not in tables:
        op.create_table(
            'job_questions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_offer_id', sa.Integer(), nullable=False),
            sa.Column('question', sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Check which tables exist before dropping
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    # Drop tables in reverse order of creation if they exist
    if 'job_questions' in tables:
        op.drop_table('job_questions')
    if 'job_requirements' in tables:
        op.drop_table('job_requirements')
    if 'job_offers' in tables:
        op.drop_table('job_offers')
    if 'companies' in tables:
        op.drop_table('companies')
