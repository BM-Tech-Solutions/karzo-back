from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base class for Report shared properties
class ReportBase(BaseModel):
    interview_id: int
    candidate_id: int
    score: Optional[int] = None
    duration: Optional[str] = None
    feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    improvements: Optional[List[str]] = None

# Properties to receive via API on creation
class ReportCreate(ReportBase):
    pass

# Properties to receive via API on update
class ReportUpdate(BaseModel):
    score: Optional[int] = None
    duration: Optional[str] = None
    feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    improvements: Optional[List[str]] = None

# Properties shared by models stored in DB
class ReportInDBBase(ReportBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Properties to return to client
class Report(ReportInDBBase):
    pass

# Properties stored in DB
class ReportInDB(ReportInDBBase):
    pass
