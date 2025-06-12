from pydantic import BaseModel
from typing import Optional, List

class JobQuestionBase(BaseModel):
    question: str

class JobQuestionCreate(JobQuestionBase):
    pass

class JobQuestionRead(JobQuestionBase):
    id: int
    job_offer_id: int

    class Config:
        from_attributes = True

class JobRequirementBase(BaseModel):
    requirement: str

class JobRequirementCreate(JobRequirementBase):
    pass

class JobRequirementRead(JobRequirementBase):
    id: int
    job_offer_id: int

    class Config:
        from_attributes = True

class JobOfferBase(BaseModel):
    title: str
    description: str

class JobOfferCreate(JobOfferBase):
    requirements: List[str] = []
    questions: List[str] = []

class JobOfferUpdate(JobOfferBase):
    requirements: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    title: Optional[str] = None
    description: Optional[str] = None

class JobOfferRead(JobOfferBase):
    id: int
    company_id: int
    is_active: bool
    status: str = "active"  # Default status if not provided
    requirements: List[JobRequirementRead] = []
    questions: List[JobQuestionRead] = []

    class Config:
        from_attributes = True

class CandidateInvitation(BaseModel):
    email: str
    job_offer_id: int
