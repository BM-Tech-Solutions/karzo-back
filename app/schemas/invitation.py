from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InvitationBase(BaseModel):
    email: str
    status: Optional[str] = "pending"

class InvitationCreate(InvitationBase):
    pass

class InvitationUpdate(BaseModel):
    status: Optional[str] = None

class InvitationRead(InvitationBase):
    id: int
    company_id: int
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        orm_mode = True
