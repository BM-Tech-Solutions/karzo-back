from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: str = "candidate"  # <-- Add this line

class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str

    class Config:
        from_attributes = True