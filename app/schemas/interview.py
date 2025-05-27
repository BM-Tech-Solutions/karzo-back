from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class InterviewBase(BaseModel):
    candidate_id: int
    job_id: int
    date: datetime
    status: str = "scheduled"

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    date: Optional[datetime] = None
    status: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[int] = None

class Interview(InterviewBase):
    id: int
    feedback: Optional[str] = None
    score: Optional[int] = None
    
    class Config:
        orm_mode = True

class InterviewWithDetails(Interview):
    job_title: str
    company: str
    
    class Config:
        orm_mode = True