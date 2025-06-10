from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    job_offer_id = Column(Integer, ForeignKey("job_offers.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="completed")  
    feedback = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    
    # Relationships
    candidate = relationship("User", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    job_offer = relationship("JobOffer", back_populates="interviews")