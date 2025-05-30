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
    status: str = "processing"  # Default to processing
    conversation_id: Optional[str] = None
    transcript: Optional[List[Dict[str, Any]]] = None
    transcript_summary: Optional[str] = None

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
    status: Optional[str] = None
    conversation_id: Optional[str] = None
    transcript: Optional[List[Dict[str, Any]]] = None
    transcript_summary: Optional[str] = None

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

# Schema for generating a report from a transcript
class GenerateReportRequest(BaseModel):
    report_id: int
    conversation_id: str
    elevenlabs_api_key: Optional[str] = None
