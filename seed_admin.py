import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import get_password_hash

def seed_admin():
    # Use localhost instead of 'db' for local execution
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "karzo")
    host = "localhost"  # Use localhost when running outside Docker
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "karzo")
    
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