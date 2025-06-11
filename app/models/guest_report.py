from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class GuestReport(Base):
    """
    Model for reports generated from guest interviews.
    This is separate from the main Report model to avoid foreign key constraints.
    """
    __tablename__ = "guest_reports"

    id = Column(Integer, primary_key=True, index=True)
    guest_interview_id = Column(Integer, ForeignKey("guest_interviews.id"), nullable=False)
    candidate_email = Column(String, nullable=False)
    score = Column(Integer, nullable=True)
    duration = Column(String, nullable=True)
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)  # Store as JSON array
    improvements = Column(JSON, nullable=True)  # Store as JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False, default="processing")  # processing, complete
    conversation_id = Column(String, nullable=True)  # ElevenLabs conversation ID
    transcript = Column(JSON, nullable=True)  # Full conversation transcript
    transcript_summary = Column(Text, nullable=True)  # Summary of the transcript
    error_message = Column(Text, nullable=True)  # Error message if status is failed
    
    # Relationships
    guest_interview = relationship("GuestInterview", backref="guest_report")
