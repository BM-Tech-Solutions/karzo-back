import os
from dotenv import load_dotenv  # <-- Add this line
load_dotenv()                   # <-- Add this line

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def seed_admin():
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_NAME", "Admin")
    admin_role = "admin"

    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == admin_email).first()
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
        db.add(user)
        db.commit()
        print(f"Admin user {admin_email} created successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()