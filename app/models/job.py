from sqlalchemy import Column, Integer, String, Text, Date
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import date

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String, index=True)
    description = Column(Text)
    posted_date = Column(Date, default=date.today)
    
    # Define relationship with requirements
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")