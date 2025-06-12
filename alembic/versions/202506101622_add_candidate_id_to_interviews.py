"""add_candidate_id_to_interviews

Revision ID: 202506101622
Revises: c1d2e3f4g5h6
Create Date: 2025-06-10 16:22:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202506101622'
down_revision = 'a1b2c3d4e5f6'  # Updated to use the current head as parent
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL to check if constraint exists and add it if it doesn't
    # This approach is more resilient to transaction errors
    from sqlalchemy import text
    
    # Check if the constraint exists
    conn = op.get_bind()
    
    # First check if the column exists
    has_column = conn.execute(text(
        "SELECT column_name FROM information_schema.columns " 
        "WHERE table_name='interviews' AND column_name='candidate_id'"
    )).fetchone() is not None
    
    if not has_column:
        # Add the column if it doesn't exist
        conn.execute(text("ALTER TABLE interviews ADD COLUMN candidate_id INTEGER"))
    
    # Check if the constraint exists
    has_constraint = conn.execute(text(
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name='interviews' AND constraint_name='fk_interviews_candidate_id_users'"
    )).fetchone() is not None
    
    if not has_constraint:
        # Add the foreign key constraint if it doesn't exist
        conn.execute(text(
            "ALTER TABLE interviews " 
            "ADD CONSTRAINT fk_interviews_candidate_id_users " 
            "FOREIGN KEY (candidate_id) REFERENCES users(id)"
        ))
        
    # Commit the transaction
    conn.execute(text("COMMIT"))
    
    # Log that the migration was successful
    print("Migration completed successfully - candidate_id column and foreign key constraint added or verified.")



def downgrade():
    # Use raw SQL to check if constraint exists and remove it if it does
    from sqlalchemy import text
    
    conn = op.get_bind()
    
    # Check if the constraint exists
    has_constraint = conn.execute(text(
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name='interviews' AND constraint_name='fk_interviews_candidate_id_users'"
    )).fetchone() is not None
    
    if has_constraint:
        # Remove the constraint if it exists
        conn.execute(text("ALTER TABLE interviews DROP CONSTRAINT fk_interviews_candidate_id_users"))
        
    # We don't remove the column as it might be used by existing data
    
    # Commit the transaction
    conn.execute(text("COMMIT"))
    
    print("Downgrade completed successfully - foreign key constraint removed if it existed.")
