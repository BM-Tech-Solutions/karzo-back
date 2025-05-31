import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.interview import Interview
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.report import Report
from app.core.security import get_password_hash

def seed_admin():
    # Get database connection parameters from environment variables
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    # Check if running in Docker or locally
    host = os.getenv("POSTGRES_HOST")  # Use environment variable or default to 'db' for Docker
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")
    
    # Create a direct database URL for local connection
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    print(f"Connecting to: {database_url}")
    
    # Create a new session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_NAME", "Admin")
    admin_role = "admin"
    
    try:
        existing = db_session.query(User).filter(User.email == admin_email).first()
        if existing:
            print(f"Admin user with email {admin_email} already exists.")
            return

        user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            full_name=admin_name,
            role=admin_role,
            is_active=1,
        )
        db_session.add(user)
        db_session.commit()
        print(f"Admin user {admin_email} created successfully.")
    finally:
        db_session.close()

if __name__ == "__main__":
    seed_admin()