"""Add TTS parameters to invitations

Revision ID: 20250204_add_tts_parameters
Revises: 20250204_add_language_field
Create Date: 2025-02-04 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250204_add_tts_parameters'
down_revision = '20250204_add_language_field'
branch_labels = None
depends_on = None


def upgrade():
    # Add TTS parameter columns to invitations table
    op.add_column('invitations', sa.Column('tts_temperature', sa.Float(), nullable=True))
    op.add_column('invitations', sa.Column('tts_stability', sa.Float(), nullable=True))
    op.add_column('invitations', sa.Column('tts_speed', sa.Float(), nullable=True))
    op.add_column('invitations', sa.Column('tts_similarity_boost', sa.Float(), nullable=True))


def downgrade():
    # Remove TTS parameter columns from invitations table
    op.drop_column('invitations', 'tts_similarity_boost')
    op.drop_column('invitations', 'tts_speed')
    op.drop_column('invitations', 'tts_stability')
    op.drop_column('invitations', 'tts_temperature')
