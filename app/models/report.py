from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
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
    
    # Relationships
    interview = relationship("Interview", backref="report")
    candidate = relationship("User", backref="reports")
