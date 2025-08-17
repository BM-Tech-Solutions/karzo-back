from sqlalchemy import Column, Integer, String, Text, Boolean
from app.db.base import Base
from sqlalchemy.orm import relationship

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    size = Column(String, nullable=True)  # Small, Medium, Large, Enterprise
    sector = Column(String, nullable=True)  # Industry sector
    about = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    # API key used for external integrations (prefixed with "karzo-")
    api_key = Column(String, unique=True, nullable=True, index=True)
    # Optional parent identifier for hierarchical grouping
    parent_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    job_offers = relationship("JobOffer", back_populates="company")
    invitations = relationship("Invitation", back_populates="company")
    applications = relationship("Application", back_populates="company")
