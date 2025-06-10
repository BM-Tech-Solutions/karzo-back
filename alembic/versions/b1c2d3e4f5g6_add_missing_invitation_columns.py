"""add_missing_invitation_columns

Revision ID: b1c2d3e4f5g6
Revises: 9d8e7f6a5b4c
Create Date: 2025-06-10 10:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, None] = '9d8e7f6a5b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We need to inspect the database to see what columns already exist
    from sqlalchemy import inspect
    from sqlalchemy import create_engine
    from sqlalchemy.engine import reflection
    import os
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = 'postgresql+psycopg2://postgres:karzo@db:5432/karzo'
    
    # Create engine and inspector
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    # Get existing columns in invitations table
    existing_columns = []
    try:
        existing_columns = inspector.get_columns('invitations')
        existing_column_names = [col['name'] for col in existing_columns]
        print(f"Existing columns: {existing_column_names}")
    except Exception as e:
        print(f"Error inspecting table: {str(e)}")
        # If we can't inspect, assume table doesn't exist yet
        existing_column_names = []
    
    # Add email column if it doesn't exist
    if 'email' not in existing_column_names:
        op.add_column('invitations', sa.Column('email', sa.String(), nullable=False, server_default=''))
        print("Added email column")
    
    # Add status column if it doesn't exist
    if 'status' not in existing_column_names:
        op.add_column('invitations', sa.Column('status', sa.String(), nullable=False, server_default='pending'))
        print("Added status column")
    
    # Add created_at column if it doesn't exist
    if 'created_at' not in existing_column_names:
        op.add_column('invitations', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')))
        print("Added created_at column")
    
    # Add expires_at column if it doesn't exist
    if 'expires_at' not in existing_column_names:
        op.add_column('invitations', sa.Column('expires_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW() + INTERVAL \'7 days\'')))
        print("Added expires_at column")
    
    # Add token column if it doesn't exist
    if 'token' not in existing_column_names:
        op.add_column('invitations', sa.Column('token', sa.String(), nullable=False, server_default=''))
        print("Added token column")
    
    # Add message column if it doesn't exist
    if 'message' not in existing_column_names:
        op.add_column('invitations', sa.Column('message', sa.Text(), nullable=True))
        print("Added message column")
    
    # Add resend_count column if it doesn't exist
    if 'resend_count' not in existing_column_names:
        op.add_column('invitations', sa.Column('resend_count', sa.Integer(), nullable=False, server_default='0'))
        print("Added resend_count column")
    
    # Add last_sent_at column if it doesn't exist
    if 'last_sent_at' not in existing_column_names:
        op.add_column('invitations', sa.Column('last_sent_at', sa.DateTime(), nullable=True))
        print("Added last_sent_at column")
    
    # Check if indices exist before creating them
    existing_indices = []
    try:
        existing_indices = inspector.get_indexes('invitations')
        existing_index_names = [idx['name'] for idx in existing_indices]
        print(f"Existing indices: {existing_index_names}")
    except Exception as e:
        print(f"Error inspecting indices: {str(e)}")
        existing_index_names = []
    
    # Create index on token if it doesn't exist
    if 'ix_invitations_token' not in existing_index_names:
        op.create_index(op.f('ix_invitations_token'), 'invitations', ['token'], unique=False)
        print("Added token index")
    
    # Create index on email if it doesn't exist
    if 'ix_invitations_email' not in existing_index_names:
        op.create_index(op.f('ix_invitations_email'), 'invitations', ['email'], unique=False)
        print("Added email index")



def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_invitations_email'), table_name='invitations')
    op.drop_index(op.f('ix_invitations_token'), table_name='invitations')
    
    # Drop columns
    op.drop_column('invitations', 'last_sent_at')
    op.drop_column('invitations', 'resend_count')
    op.drop_column('invitations', 'message')
    op.drop_column('invitations', 'token')
    op.drop_column('invitations', 'expires_at')
    op.drop_column('invitations', 'created_at')
    op.drop_column('invitations', 'status')
    op.drop_column('invitations', 'email')
