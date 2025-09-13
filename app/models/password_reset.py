from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.base import Base
from datetime import datetime

class CompanyPasswordReset(Base):
    __tablename__ = "company_password_resets"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
