from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.company import CompanyCreate, CompanyRead, CompanyLogin
from app.crud.company import create_company, authenticate_company, get_company_by_email
from app.db.session import get_db
from app.core.security import create_access_token, verify_token
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

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
