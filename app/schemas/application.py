from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class ApplicationBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    cover_letter: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationWithToken(ApplicationBase):
    invitation_token: str


class ApplicationInDB(ApplicationBase):
    id: int
    company_id: int
    job_offer_id: Optional[int] = None
    invitation_id: Optional[int] = None
    status: str
    created_at: datetime
    resume_path: Optional[str] = None

    class Config:
        orm_mode = True


class ApplicationRead(ApplicationInDB):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
