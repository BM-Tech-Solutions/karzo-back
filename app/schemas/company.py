from pydantic import BaseModel, EmailStr
from typing import Optional, List

class CompanyBase(BaseModel):
    name: str
    email: EmailStr
    size: Optional[str] = None
    sector: Optional[str] = None
    about: Optional[str] = None
    website: Optional[str] = None

class CompanyCreate(CompanyBase):
    password: str

class CompanyUpdate(CompanyBase):
    password: Optional[str] = None

class CompanyRead(CompanyBase):
    id: int
    is_active: bool
    api_key: Optional[str] = None

    class Config:
        from_attributes = True

class CompanyLogin(BaseModel):
    email: EmailStr
    password: str
