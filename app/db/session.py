from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
import time

# Get database connection parameters from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "karzo")
POSTGRES_DB = os.getenv("POSTGRES_DB", "karzo")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")  # This should be 'db' in Docker
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Construct database URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Print connection details for debugging
print(f"Connecting to database with URL: {DATABASE_URL}", file=sys.stderr)
print(f"Environment variables: HOST={POSTGRES_HOST}, DB={POSTGRES_DB}, USER={POSTGRES_USER}", file=sys.stderr)

# Add retry logic for database connection
max_retries = 5
retry_count = 0
while retry_count < max_retries:
    try:
        # Create SQLAlchemy engine with connection pooling and timeout settings
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=3600,   # Recycle connections after 1 hour
            connect_args={
                "connect_timeout": 10  # Connection timeout in seconds
            }
        )
        
        # Test the connection - using text() to create an executable SQL statement
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("Database connection successful!", file=sys.stderr)
            break
    except Exception as e:
        retry_count += 1
        print(f"Database connection attempt {retry_count} failed: {str(e)}", file=sys.stderr)
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Retrying in {wait_time} seconds...", file=sys.stderr)
            time.sleep(wait_time)
        else:
            print("All database connection attempts failed.", file=sys.stderr)
            # Continue with engine creation anyway, will fail later if still can't connect

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()