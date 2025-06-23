from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class GuestCandidate(Base):
    """
    Model for guest candidates who apply through invitations without creating a full user account.
    This allows candidates to receive multiple invitations for different positions.
    """
    __tablename__ = "guest_candidates"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    candidate_summary = Column(Text, nullable=True)  # Summary generated from CV
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="guest_candidate")
    interviews = relationship("GuestInterview", back_populates="guest_candidate")


class GuestInterview(Base):
    """
    Model for interviews with guest candidates.
    This is separate from the main Interview model to avoid constraints issues.
    """
    __tablename__ = "guest_interviews"

    id = Column(Integer, primary_key=True, index=True)
    guest_candidate_id = Column(Integer, ForeignKey("guest_candidates.id"))
    job_offer_id = Column(Integer, ForeignKey("job_offers.id"))
    date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  
    feedback = Column(Text, nullable=True)
    score = Column(Integer, nullable=True, default=0)
    
    # Fields for report generation
    conversation_id = Column(String, nullable=True)
    report_id = Column(String, nullable=True)
    report_status = Column(String, nullable=True)
    candidate_summary = Column(Text, nullable=True)  # Summary for ElevenLabs interview
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    guest_candidate = relationship("GuestCandidate", back_populates="interviews")
    job_offer = relationship("JobOffer", back_populates="guest_interviews")
