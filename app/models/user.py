from sqlalchemy import Column, Integer, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)  # Add this line
    resume_url = Column(String, nullable=True)  # Add this line
    is_active = Column(Integer, default=1)
    role = Column(String, nullable=False, default="candidate")