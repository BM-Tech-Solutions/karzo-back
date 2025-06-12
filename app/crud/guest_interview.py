from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_
import logging
from datetime import datetime

from app.models.guest_candidate import GuestCandidate, GuestInterview
from app.models.job_offer import JobOffer
from app.models.company import Company

logger = logging.getLogger(__name__)

def get_guest_interview_by_id(db: Session, interview_id: int) -> Optional[GuestInterview]:
    """Get a guest interview by ID"""
    return db.query(GuestInterview).filter(GuestInterview.id == interview_id).first()

def get_guest_interviews_by_candidate(db: Session, guest_candidate_id: int) -> List[GuestInterview]:
    """Get all interviews for a specific guest candidate"""
    return db.query(GuestInterview).filter(GuestInterview.guest_candidate_id == guest_candidate_id).all()

def get_guest_interviews_by_company(db: Session, company_id: int) -> List[Dict[str, Any]]:
    """
    Get all guest interviews for a specific company with candidate and job offer details
    """
    try:
        results = db.query(
            GuestInterview.id,
            GuestInterview.guest_candidate_id,
            GuestCandidate.full_name.label('candidate_name'),
            GuestCandidate.email.label('candidate_email'),
            GuestInterview.job_offer_id,
            JobOffer.title.label('job_title'),
            GuestInterview.date,
            GuestInterview.status,
            GuestInterview.conversation_id,
            GuestInterview.report_id,
            GuestInterview.report_status
        ).join(
            GuestCandidate, GuestCandidate.id == GuestInterview.guest_candidate_id
        ).join(
            JobOffer, JobOffer.id == GuestInterview.job_offer_id
        ).filter(
            JobOffer.company_id == company_id
        ).all()
        
        # Transform results to dictionary format
        interviews = []
        for result in results:
            interview = {
                "id": result.id,
                "candidate_id": result.guest_candidate_id,
                "candidate_name": result.candidate_name,
                "candidate_email": result.candidate_email,
                "job_offer_id": result.job_offer_id,
                "job_title": result.job_title,
                "date": result.date.isoformat() if result.date else None,
                "status": result.status,
                "conversation_id": result.conversation_id,
                "report_id": result.report_id,
                "report_status": result.report_status
            }
            interviews.append(interview)
            
        return interviews
    except Exception as e:
        logger.error(f"Error getting guest interviews by company: {str(e)}")
        return []

def update_guest_interview_status(db: Session, interview_id: int, status: str) -> Optional[GuestInterview]:
    """Update the status of a guest interview"""
    interview = get_guest_interview_by_id(db, interview_id)
    if interview:
        interview.status = status
        db.commit()
        db.refresh(interview)
    return interview

def update_guest_interview_report(
    db: Session, 
    interview_id: int, 
    report_id: str, 
    report_status: str
) -> Optional[GuestInterview]:
    """Update the report information for a guest interview"""
    interview = get_guest_interview_by_id(db, interview_id)
    if interview:
        interview.report_id = report_id
        interview.report_status = report_status
        db.commit()
        db.refresh(interview)
    return interview
