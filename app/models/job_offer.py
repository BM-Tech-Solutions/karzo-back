from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from typing import List

class JobOffer(Base):
    __tablename__ = "job_offers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    is_active = Column(Boolean, default=True)
    status = Column(String, default="active")
    
    # Relationships
    company = relationship("Company", back_populates="job_offers")
    requirements = relationship("JobRequirement", back_populates="job_offer")
    questions = relationship("JobQuestion", back_populates="job_offer")
    interviews = relationship("Interview", back_populates="job_offer")
    invitations = relationship("Invitation", back_populates="job_offer")
    applications = relationship("Application", back_populates="job_offer")

class JobQuestion(Base):
    __tablename__ = "job_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    job_offer_id = Column(Integer, ForeignKey("job_offers.id"))
    
    # Relationships
    job_offer = relationship("JobOffer", back_populates="questions")
