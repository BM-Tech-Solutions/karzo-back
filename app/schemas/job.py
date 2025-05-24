from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class JobRequirementBase(BaseModel):
    requirement: str

class JobRequirementCreate(JobRequirementBase):
    pass

class JobRequirement(JobRequirementBase):
    id: int
    job_id: int

    class Config:
        orm_mode = True

class JobBase(BaseModel):
    title: str
    company: str
    location: str
    description: str

class JobCreate(JobBase):
    requirements: List[str]

class JobUpdate(JobBase):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None

class Job(JobBase):
    id: int
    posted_date: date
    requirements: List[str]

    class Config:
        orm_mode = True