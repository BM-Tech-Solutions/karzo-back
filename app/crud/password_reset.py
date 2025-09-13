from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.models.password_reset import CompanyPasswordReset
from app.models.company import Company

CODE_TTL_MINUTES = 15
MAX_ATTEMPTS_PER_HOUR = 5

def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"

def create_reset_code(db: Session, email: str) -> str:
    # Ensure company exists
    company = db.query(Company).filter(Company.email == email).first()
    if not company:
        return ""

    # Optional: rate limit by counting codes in the last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_count = (
        db.query(CompanyPasswordReset)
        .filter(CompanyPasswordReset.email == email)
        .filter(CompanyPasswordReset.created_at >= one_hour_ago)
        .count()
    )
    if recent_count >= MAX_ATTEMPTS_PER_HOUR:
        raise ValueError("Too many attempts. Please try again later.")

    code = _generate_code()
    expires = datetime.utcnow() + timedelta(minutes=CODE_TTL_MINUTES)

    rec = CompanyPasswordReset(email=email, code=code, expires_at=expires)
    db.add(rec)
    db.commit()
    return code


def verify_code(db: Session, email: str, code: str) -> bool:
    rec = (
        db.query(CompanyPasswordReset)
        .filter(CompanyPasswordReset.email == email)
        .filter(CompanyPasswordReset.code == code)
        .order_by(CompanyPasswordReset.id.desc())
        .first()
    )
    if not rec:
        return False
    if rec.used:
        return False
    if rec.expires_at < datetime.utcnow():
        return False
    return True


def mark_code_used(db: Session, email: str, code: str) -> None:
    rec = (
        db.query(CompanyPasswordReset)
        .filter(CompanyPasswordReset.email == email)
        .filter(CompanyPasswordReset.code == code)
        .order_by(CompanyPasswordReset.id.desc())
        .first()
    )
    if rec:
        rec.used = True
        db.add(rec)
        db.commit()
