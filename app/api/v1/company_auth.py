from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.company import CompanyCreate, CompanyRead, CompanyLogin
from app.crud.company import create_company, authenticate_company, get_company_by_email
from app.db.session import get_db
from app.core.security import create_access_token, verify_token, get_password_hash
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetVerify,
    PasswordResetConfirm,
)
from app.crud.password_reset import (
    create_reset_code,
    verify_code,
    mark_code_used,
)
from app.utils.email import send_password_reset_code

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/register", response_model=CompanyRead)
def register_company(company_in: CompanyCreate, db: Session = Depends(get_db)):
    # Check if company with this email already exists
    db_company = get_company_by_email(db, company_in.email)
    if db_company:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    company = create_company(db, company_in)
    return company

@router.post("/login")
def login_company(company_in: CompanyLogin, db: Session = Depends(get_db)):
    company = authenticate_company(db, company_in.email, company_in.password)
    if not company:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": company.email, "type": "company"})
    company_data = CompanyRead.from_orm(company)
    
    return {
        "access_token": access_token,
        "company": company_data
    }

@router.get("/validate-token")
@router.get("/validate-token/")
async def validate_company_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    company = get_company_by_email(db, email)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"valid": True}

# Get current company from token
async def get_current_company(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    company = get_company_by_email(db, email)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

# ------------------------
# Forgot Password Endpoints
# ------------------------

@router.post("/forgot-password/request")
def company_forgot_password_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    # Always act like success to avoid email enumeration, but only send when company exists
    company = get_company_by_email(db, payload.email)
    if company:
        try:
            code = create_reset_code(db, payload.email)
            if code:
                send_password_reset_code(payload.email, code)
        except ValueError:
            # Rate-limited; still return success message to avoid information leakage
            pass
    return {"message": "If an account with that email exists, a code has been sent."}


@router.post("/forgot-password/verify")
def company_forgot_password_verify(payload: PasswordResetVerify, db: Session = Depends(get_db)):
    # Return valid flag without revealing if email exists
    ok = verify_code(db, payload.email, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    return {"valid": True}


@router.post("/forgot-password/reset")
def company_forgot_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    # Verify code
    ok = verify_code(db, payload.email, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    company = get_company_by_email(db, payload.email)
    if not company:
        # Generic error to avoid leaking existence
        raise HTTPException(status_code=400, detail="Invalid request")

    # Update password
    company.hashed_password = get_password_hash(payload.new_password)
    db.add(company)
    db.commit()

    # Mark code used
    mark_code_used(db, payload.email, payload.code)

    return {"message": "Password has been reset successfully"}
