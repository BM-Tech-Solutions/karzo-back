from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class InvitationBase(BaseModel):
    email: str
    status: str = "pending"
    message: Optional[str] = None

class InvitationCreate(InvitationBase):
    job_offer_id: Optional[int] = None

class InvitationBulkCreate(BaseModel):
    emails: list[str]
    job_offer_id: Optional[int] = None
    message: Optional[str] = None

class InvitationUpdate(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None

class InvitationRead(InvitationBase):
    id: int
    company_id: int
    job_offer_id: Optional[int] = None
    created_at: datetime
    expires_at: datetime
    token: str
    resend_count: int = 0
    last_sent_at: Optional[datetime] = None
    job_title: Optional[str] = None  # This will be populated from the relationship

    class Config:
        orm_mode = True

class InvitationPublic(BaseModel):
    """Schema for public invitation view (for candidates)"""
    id: int
    token: str
    company_id: int
    company_name: str
    job_offer_id: Optional[int] = None
    job_title: Optional[str] = None
    status: str
    candidate_email: str
    message: Optional[str] = None
    expires_at: datetime
    
    class Config:
        orm_mode = True
