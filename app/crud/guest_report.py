from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.models.guest_report import GuestReport
from datetime import datetime

def create_guest_report(
    db: Session,
    guest_interview_id: int,
    candidate_email: str,
    conversation_id: str = None
) -> GuestReport:
    """
    Create a new guest report
    """
    db_report = GuestReport(
        guest_interview_id=guest_interview_id,
        candidate_email=candidate_email,
        status="processing",
        conversation_id=conversation_id,
        created_at=datetime.utcnow()
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_guest_report(db: Session, report_id: int) -> Optional[GuestReport]:
    """
    Get a guest report by ID
    """
    return db.query(GuestReport).filter(GuestReport.id == report_id).first()

def get_guest_report_by_interview_id(db: Session, guest_interview_id: int) -> Optional[GuestReport]:
    """
    Get a guest report by guest interview ID
    """
    return db.query(GuestReport).filter(GuestReport.guest_interview_id == guest_interview_id).first()

def update_guest_report_status(
    db: Session,
    report_id: int,
    status: str
) -> Optional[GuestReport]:
    """
    Update the status of a guest report
    """
    db_report = get_guest_report(db, report_id=report_id)
    if db_report:
        db_report.status = status
        db.commit()
        db.refresh(db_report)
    return db_report

def update_guest_report_content(
    db: Session,
    report_id: int,
    content: Dict[str, Any]
) -> Optional[GuestReport]:
    """
    Update the content of a guest report
    """
    db_report = get_guest_report(db, report_id=report_id)
    if db_report:
        for key, value in content.items():
            if hasattr(db_report, key):
                setattr(db_report, key, value)
        db.commit()
        db.refresh(db_report)
    return db_report
