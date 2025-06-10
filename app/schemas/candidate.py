from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CandidateBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    resume_url: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    resume_url: Optional[str] = None

class CandidateRead(CandidateBase):
    id: int
    is_active: Optional[int] = 1
    
    class Config:
        from_attributes = True  # Updated from orm_mode=True for Pydantic v2
