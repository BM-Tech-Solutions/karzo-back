from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class InvitationBase(BaseModel):
    email: str
    status: str = "pending"
    message: Optional[str] = None

class InvitationCreate(InvitationBase):
    job_offer_id: Optional[int] = None
    # External company information (when inviting for another company)
    external_company_name: Optional[str] = None
    external_company_email: Optional[EmailStr] = None
    external_company_size: Optional[str] = None
    external_company_sector: Optional[str] = None
    external_company_about: Optional[str] = None
    external_company_website: Optional[str] = None

class InvitationBulkCreate(BaseModel):
    emails: list[str]
    job_offer_id: Optional[int] = None
    message: Optional[str] = None
    # External company information (when inviting for another company)
    external_company_name: Optional[str] = None
    external_company_email: Optional[EmailStr] = None
    external_company_size: Optional[str] = None
    external_company_sector: Optional[str] = None
    external_company_about: Optional[str] = None
    external_company_website: Optional[str] = None

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
    job_questions: List[str] = []
    status: str
    candidate_email: str
    message: Optional[str] = None
    expires_at: datetime
    # External company fields
    external_company_name: Optional[str] = None
    external_company_email: Optional[str] = None
    external_company_size: Optional[str] = None
    external_company_sector: Optional[str] = None
    external_company_about: Optional[str] = None
    external_company_website: Optional[str] = None
    
    class Config:
        orm_mode = True
