from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import and_, or_
import logging

from app.models.guest_candidate import GuestCandidate, GuestInterview
from app.models.job_offer import JobOffer
from app.models.company import Company

logger = logging.getLogger(__name__)

def get_guest_candidate_by_email(db: Session, email: str) -> Optional[GuestCandidate]:
    """Get a guest candidate by email"""
    return db.query(GuestCandidate).filter(GuestCandidate.email == email).first()

def get_guest_candidate_by_id(db: Session, guest_candidate_id: int) -> Optional[GuestCandidate]:
    """Get a guest candidate by ID"""
    return db.query(GuestCandidate).filter(GuestCandidate.id == guest_candidate_id).first()

def get_guest_candidates_by_job_offers(
    db: Session, job_offer_ids: List[int], company_id: int
) -> List[dict]:
    """
    Get all guest candidates who have applied to the specified job offers
    """
    try:
        # Query to get guest candidates with their latest interview status
        results = db.query(
            GuestCandidate.id,
            GuestCandidate.full_name,
            GuestCandidate.email,
            GuestCandidate.phone,
            GuestCandidate.resume_url,
            GuestInterview.status,
            GuestInterview.job_offer_id,
            JobOffer.title.label('job_title')
        ).join(
            GuestInterview, GuestInterview.guest_candidate_id == GuestCandidate.id
        ).join(
            JobOffer, JobOffer.id == GuestInterview.job_offer_id
        ).filter(
            and_(
                GuestInterview.job_offer_id.in_(job_offer_ids),
                JobOffer.company_id == company_id
            )
        ).all()
        
        # Transform results to dictionary format
        candidates = []
        for result in results:
            candidate = {
                "id": result.id,
                "name": result.full_name,
                "email": result.email,
                "phone": result.phone,
                "resume_url": result.resume_url,
                "status": result.status,
                "job_offer_id": result.job_offer_id,
                "job_title": result.job_title
            }
            candidates.append(candidate)
            
        return candidates
    except Exception as e:
        logger.error(f"Error getting guest candidates by job offers: {str(e)}")
        return []

def get_passed_guest_candidates_by_job_offers(
    db: Session, job_offer_ids: List[int], company_id: int
) -> List[dict]:
    """
    Get all guest candidates who have passed interviews for the specified job offers
    """
    try:
        # Query to get guest candidates with passed interviews
        results = db.query(
            GuestCandidate.id,
            GuestCandidate.full_name,
            GuestCandidate.email,
            GuestCandidate.phone,
            GuestCandidate.resume_url,
            GuestInterview.status,
            GuestInterview.job_offer_id,
            JobOffer.title.label('job_title')
        ).join(
            GuestInterview, GuestInterview.guest_candidate_id == GuestCandidate.id
        ).join(
            JobOffer, JobOffer.id == GuestInterview.job_offer_id
        ).filter(
            and_(
                GuestInterview.job_offer_id.in_(job_offer_ids),
                JobOffer.company_id == company_id,
                GuestInterview.status == "passed"
            )
        ).all()
        
        # Transform results to dictionary format
        candidates = []
        for result in results:
            candidate = {
                "id": result.id,
                "name": result.full_name,
                "email": result.email,
                "phone": result.phone,
                "resume_url": result.resume_url,
                "status": result.status,
                "job_offer_id": result.job_offer_id,
                "job_title": result.job_title
            }
            candidates.append(candidate)
            
        return candidates
    except Exception as e:
        logger.error(f"Error getting passed guest candidates by job offers: {str(e)}")
        return []
