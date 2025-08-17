from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class InvitationBase(BaseModel):
    email: str
    status: str = "pending"
    message: Optional[str] = None

class InvitationCreate(InvitationBase):
    job_offer_id: Optional[int] = None
    # Language field
    language: Optional[str] = None
    # TTS parameters for ElevenLabs voice configuration
    tts_temperature: Optional[float] = Field(None, ge=0, le=1, description="LLM temperature (0-1)")
    tts_stability: Optional[float] = Field(None, ge=0, le=1, description="Voice stability (0-1)")
    tts_speed: Optional[float] = Field(None, ge=0.25, le=4.0, description="Speaking speed (0.25-4.0)")
    tts_similarity_boost: Optional[float] = Field(None, ge=0, le=1, description="Voice similarity (0-1)")
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
    # Language field
    language: Optional[str] = None
    # TTS parameters for ElevenLabs voice configuration
    tts_temperature: Optional[float] = Field(None, ge=0, le=1, description="LLM temperature (0-1)")
    tts_stability: Optional[float] = Field(None, ge=0, le=1, description="Voice stability (0-1)")
    tts_speed: Optional[float] = Field(None, ge=0.25, le=4.0, description="Speaking speed (0.25-4.0)")
    tts_similarity_boost: Optional[float] = Field(None, ge=0, le=1, description="Voice similarity (0-1)")
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

class ExistingCandidate(BaseModel):
    """Schema for existing candidate info"""
    id: int
    full_name: str
    phone: Optional[str] = None

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
    # Candidate existence check
    candidate_exists: bool = False
    existing_candidate: Optional[ExistingCandidate] = None
    # Language field
    language: Optional[str] = None
    # TTS parameters for ElevenLabs voice configuration
    tts_temperature: Optional[float] = None
    tts_stability: Optional[float] = None
    tts_speed: Optional[float] = None
    tts_similarity_boost: Optional[float] = None
    # External company fields
    external_company_name: Optional[str] = None
    external_company_email: Optional[str] = None
    external_company_size: Optional[str] = None
    external_company_sector: Optional[str] = None
    external_company_about: Optional[str] = None
    external_company_website: Optional[str] = None
    
    class Config:
        orm_mode = True
