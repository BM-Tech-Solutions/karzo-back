from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base

class Application(Base):
    """Application model for candidates applying to job offers"""
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    cover_letter = Column(Text, nullable=True)
    resume_path = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, reviewed, accepted, rejected
    created_at = Column(DateTime, nullable=False)
    
    # Foreign keys
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    job_offer_id = Column(Integer, ForeignKey("job_offers.id"), nullable=True)
    invitation_id = Column(Integer, ForeignKey("invitations.id"), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="applications")
    job_offer = relationship("JobOffer", back_populates="applications")
    invitation = relationship("Invitation", back_populates="applications")
