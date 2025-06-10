from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    job_offer_id = Column(Integer, ForeignKey("job_offers.id"), nullable=True)
    email = Column(String, nullable=False)
    candidate_email = Column(String, nullable=False)  # Added to match database schema
    status = Column(String, nullable=False, default="pending")  # pending, accepted, expired
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    token = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=True)
    resend_count = Column(Integer, default=0)
    last_sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="invitations")
    job_offer = relationship("JobOffer", back_populates="invitations")
    applications = relationship("Application", back_populates="invitation")
