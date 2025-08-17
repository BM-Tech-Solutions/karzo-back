from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.invitation import Invitation
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.core.security import get_password_hash, verify_password
from typing import Optional, List, Dict, Any
from datetime import datetime
import secrets

def get_company_by_email(db: Session, email: str):
    return db.query(Company).filter(Company.email == email).first()

def get_company_by_id(db: Session, company_id: int):
    return db.query(Company).filter(Company.id == company_id).first()

def get_company_by_name(db: Session, name: str):
    return db.query(Company).filter(Company.name == name).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Company).offset(skip).limit(limit).all()

def create_company(db: Session, company_in: CompanyCreate):
    hashed_password = get_password_hash(company_in.password)
    db_company = Company(
        email=company_in.email,
        name=company_in.name,
        hashed_password=hashed_password,
        size=company_in.size,
        sector=company_in.sector,
        about=company_in.about,
        website=company_in.website
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(db: Session, company_id: int, company_in: CompanyUpdate):
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None
    
    update_data = company_in.dict(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def authenticate_company(db: Session, email: str, password: str):
    company = get_company_by_email(db, email)
    if not company or not verify_password(password, company.hashed_password):
        return None
    return company


def generate_and_set_api_key(db: Session, company_id: int) -> str:
    """Generate a unique API key with 'karzo-' prefix and save it to the company."""
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        raise ValueError("Company not found")

    # generate until unique
    while True:
        # token_urlsafe contains - and _ which are fine, but we can simplify
        raw = secrets.token_urlsafe(24)
        normalized = raw.replace("_", "").replace("-", "")
        api_key = f"karzo-{normalized}"
        existing = db.query(Company).filter(Company.api_key == api_key).first()
        if not existing:
            break

    db_company.api_key = api_key
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return api_key


def get_invitations_by_company(db: Session, company_id: int) -> List[Dict[str, Any]]:
    """
    Get all invitations sent by a company
    """
    invitations = db.query(Invitation).filter(Invitation.company_id == company_id).all()
    
    # Convert to dictionaries with formatted dates
    result = []
    for inv in invitations:
        result.append({
            "id": inv.id,
            "email": inv.email,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None
        })
    
    return result


def create_invitation(db: Session, company_id: int, invitation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new invitation for a candidate
    """
    # Create expiration date (e.g., 7 days from now)
    from datetime import timedelta
    expires_at = datetime.now() + timedelta(days=7)
    
    # Create invitation record
    invitation = Invitation(
        company_id=company_id,
        email=invitation_data.get("email"),
        status="pending",
        created_at=datetime.now(),
        expires_at=expires_at
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    return {
        "id": invitation.id,
        "email": invitation.email,
        "status": invitation.status,
        "created_at": invitation.created_at.isoformat(),
        "expires_at": invitation.expires_at.isoformat()
    }
