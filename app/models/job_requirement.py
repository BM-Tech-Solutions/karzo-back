from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(Integer, primary_key=True, index=True)
    requirement = Column(String, nullable=False)
    job_offer_id = Column(Integer, ForeignKey("job_offers.id", ondelete="CASCADE"))
    job_offer = relationship("JobOffer", back_populates="requirements")
    
    # Add relationship to Job model
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)
    job = relationship("Job", back_populates="requirements")