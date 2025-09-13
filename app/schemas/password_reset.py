from pydantic import BaseModel, EmailStr, constr

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetVerify(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6)

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6)
    new_password: constr(min_length=8)
