from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(Integer, primary_key=True, index=True)
    requirement = Column(String, nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    job = relationship("Job", back_populates="requirements")