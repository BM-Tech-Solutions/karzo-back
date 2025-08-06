from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
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
    
    # Language field
    language = Column(String, nullable=True)  # fr, en, or candidate_choice
    
    # TTS parameters for ElevenLabs voice configuration
    tts_temperature = Column(Float, nullable=True)  # LLM temperature (0-1)
    tts_stability = Column(Float, nullable=True)    # Voice stability (0-1)
    tts_speed = Column(Float, nullable=True)        # Speaking speed (0.25-4.0)
    tts_similarity_boost = Column(Float, nullable=True)  # Voice similarity (0-1)
    # External company fields
    external_company_name = Column(String, nullable=True)
    external_company_email = Column(String, nullable=True)
    external_company_size = Column(String, nullable=True)
    external_company_sector = Column(String, nullable=True)
    external_company_about = Column(Text, nullable=True)
    external_company_website = Column(String, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="invitations")
    job_offer = relationship("JobOffer", back_populates="invitations")
    applications = relationship("Application", back_populates="invitation")
