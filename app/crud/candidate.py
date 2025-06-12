from sqlalchemy.orm import Session
from sqlalchemy import distinct, func
from app.models.user import User
from app.models.interview import Interview
from app.models.job_offer import JobOffer
from typing import List, Optional, Dict, Any

def get_candidates_by_job_offers(db: Session, job_offer_ids: List[int]):
    """
    Get all candidates who have applied to the specified job offers
    
    Note: Candidates are users with role='candidate' who have interviews for the company's job offers
    """
    if not job_offer_ids:
        return []
    
    try:
        # Join User and Interview tables to get candidate information with their interviews
        # for the specified job offers
        candidates_with_interviews = db.query(
            User.id,
            User.email,
            User.full_name,
            User.phone,
            User.resume_url,
            func.count(Interview.id).label('interview_count'),
            func.max(Interview.created_at).label('last_interview')
        ).join(
            Interview, User.id == Interview.candidate_id
        ).filter(
            Interview.job_offer_id.in_(job_offer_ids),
            User.role == "candidate"
        ).group_by(
            User.id
        ).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for candidate in candidates_with_interviews:
            result.append({
                "id": candidate.id,
                "email": candidate.email,
                "full_name": candidate.full_name,
                "phone": candidate.phone,
                "resume_url": candidate.resume_url,
                "interview_count": candidate.interview_count,
                "last_interview": candidate.last_interview.isoformat() if candidate.last_interview else None,
                "is_active": 1
            })
        return result
    except Exception as e:
        print(f"Error in get_candidates_by_job_offers: {e}")
        return []


def get_candidate_applications(db: Session, candidate_id: int):
    """
    Get all job applications (interviews) for a specific candidate
    """
    try:
        # Join Interview and JobOffer tables to get application information
        applications = db.query(
            Interview.id,
            Interview.status,
            Interview.created_at,
            JobOffer.title,
            JobOffer.company_id
        ).join(
            JobOffer, Interview.job_offer_id == JobOffer.id
        ).filter(
            Interview.candidate_id == candidate_id
        ).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for app in applications:
            result.append({
                "id": app.id,
                "status": app.status,
                "created_at": app.created_at.isoformat() if app.created_at else None,
                "job_title": app.title,
                "company_id": app.company_id
            })
        return result
    except Exception as e:
        print(f"Error in get_candidate_applications: {e}")
        return []


def get_passed_candidates_by_job_offers(db: Session, job_offer_ids: List[int]):
    """
    Get candidates who have passed interviews for the specified job offers
    
    Note: These are candidates with interviews that have status='passed' or a score >= 70
    """
    if not job_offer_ids:
        return []
    
    try:
        # Join User and Interview tables to get candidate information with their passed interviews
        candidates_with_passed_interviews = db.query(
            User.id,
            User.email,
            User.full_name,
            User.phone,
            User.resume_url,
            func.max(Interview.score).label('interview_score'),
            func.max(Interview.created_at).label('last_interview')
        ).join(
            Interview, User.id == Interview.candidate_id
        ).filter(
            Interview.job_offer_id.in_(job_offer_ids),
            User.role == "candidate",
            # Either status is 'passed' or score is >= 70
            ((Interview.status == "passed") | (Interview.score >= 70))
        ).group_by(
            User.id
        ).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for candidate in candidates_with_passed_interviews:
            result.append({
                "id": candidate.id,
                "email": candidate.email,
                "full_name": candidate.full_name,
                "phone": candidate.phone,
                "resume_url": candidate.resume_url,
                "interview_score": candidate.interview_score,
                "last_interview": candidate.last_interview.isoformat() if candidate.last_interview else None,
                "status": "passed",
                "is_active": 1
            })
        return result
    except Exception as e:
        print(f"Error in get_passed_candidates_by_job_offers: {e}")
        return []
