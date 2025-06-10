from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.interview import Interview
from app.models.job import Job
from app.schemas.interview import InterviewCreate, InterviewUpdate
from typing import List, Optional
from datetime import datetime

def get_interview(db: Session, interview_id: int):
    return db.query(Interview).filter(Interview.id == interview_id).first()

def get_interviews_by_candidate(db: Session, candidate_id: int, skip: int = 0, limit: int = 100):
    # Query the database
    results = db.query(
        Interview.id,
        Interview.date,
        Interview.status,
        Job.title.label("job_title"),
        Job.company
    ).join(
        Job, Interview.job_id == Job.id
    ).filter(
        Interview.candidate_id == candidate_id
    ).offset(skip).limit(limit).all()
    
    # Convert the results to a list of dictionaries
    interviews = []
    for row in results:
        interview = {
            "id": row.id,
            "date": row.date.isoformat() if row.date else None,
            "status": row.status,
            "job_title": row.job_title,
            "company": row.company
        }
        interviews.append(interview)
    
    return interviews

def get_all_interviews(db: Session, skip: int = 0, limit: int = 100):
    # Query the database for all interviews with candidate and job details
    from app.models.user import User
    
    results = db.query(
        Interview.id,
        Interview.candidate_id,
        Interview.date,
        Interview.status,
        Job.id.label("job_id"),
        Job.title.label("job_title"),
        Job.company,
        User.full_name.label("candidate_name"),
        User.email.label("candidate_email")
    ).join(
        Job, Interview.job_id == Job.id
    ).join(
        User, Interview.candidate_id == User.id
    ).offset(skip).limit(limit).all()
    
    # Convert the results to a list of dictionaries
    interviews = []
    for row in results:
        interview = {
            "id": row.id,
            "candidate_id": row.candidate_id,
            "candidate_name": row.candidate_name,
            "candidate_email": row.candidate_email,
            "job_id": row.job_id,
            "job_title": row.job_title,
            "company": row.company,
            "date": row.date.isoformat() if row.date else None,
            "status": row.status
        }
        interviews.append(interview)
    
    return interviews

def create_interview(db: Session, interview: InterviewCreate):
    db_interview = Interview(
        candidate_id=interview.candidate_id,
        job_id=interview.job_id,
        date=interview.date,
        status=interview.status
    )
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview

def update_interview(db: Session, interview_id: int, interview: InterviewUpdate):
    db_interview = get_interview(db, interview_id)
    if db_interview:
        update_data = interview.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_interview, key, value)
        db.commit()
        db.refresh(db_interview)
    return db_interview

def delete_interview(db: Session, interview_id: int):
    db_interview = get_interview(db, interview_id)
    if db_interview:
        db.delete(db_interview)
        db.commit()
        return True
    return False

def count_unique_candidates_by_job_offers(db: Session, job_offer_ids: List[int]) -> int:
    """
    Count unique candidates who have interviews for the specified job offers
    """
    if not job_offer_ids:
        return 0
        
    # Count distinct candidate_ids where job_offer_id is in the list
    try:
        result = db.query(Interview.candidate_id).distinct().filter(
            Interview.job_offer_id.in_(job_offer_ids)
        ).count()
        return result
    except Exception as e:
        print(f"Error counting unique candidates: {e}")
        return 0

def count_pending_interviews_by_job_offers(db: Session, job_offer_ids: List[int]) -> int:
    """
    Count pending interviews for the specified job offers
    """
    if not job_offer_ids:
        return 0
        
    # Count interviews with status 'pending' where job_offer_id is in the list
    try:
        result = db.query(Interview).filter(
            Interview.job_offer_id.in_(job_offer_ids),
            Interview.status == "pending"
        ).count()
        return result
    except Exception as e:
        print(f"Error counting pending interviews: {e}")
        return 0

def get_recent_applications_by_job_offers(db: Session, job_offer_ids: List[int], limit: int = 3):
    """
    Get recent applications (interviews) for the specified job offers
    """
    if not job_offer_ids:
        return []
    
    try:
        # Import here to avoid circular imports
        from app.models.user import User
        from app.models.job_offer import JobOffer
        
        # Query recent applications with candidate and job offer details
        results = db.query(
            Interview.id,
            Interview.date,
            User.full_name.label("candidate_name"),
            JobOffer.title.label("job_title"),
            Interview.created_at
        ).join(
            User, Interview.candidate_id == User.id
        ).join(
            JobOffer, Interview.job_offer_id == JobOffer.id
        ).filter(
            Interview.job_offer_id.in_(job_offer_ids)
        ).order_by(
            Interview.created_at.desc()
        ).limit(limit).all()
        
        # Convert the results to a list of dictionaries
        applications = []
        for row in results:
            days_ago = (datetime.now() - row.created_at).days if row.created_at else 0
            application = {
                "id": row.id,
                "candidateName": row.candidate_name,
                "jobTitle": row.job_title,
                "daysAgo": days_ago
            }
            applications.append(application)
        
        return applications
    except Exception as e:
        print(f"Error getting recent applications: {e}")
        return []

def get_upcoming_interviews_by_job_offers(db: Session, job_offer_ids: List[int], limit: int = 3):
    """
    Get upcoming interviews for the specified job offers
    """
    if not job_offer_ids:
        return []
    
    try:
        # Import here to avoid circular imports
        from app.models.user import User
        from app.models.job_offer import JobOffer
        
        # Query upcoming interviews with candidate and job offer details
        results = db.query(
            Interview.id,
            Interview.date,
            User.full_name.label("candidate_name"),
            JobOffer.title.label("job_title")
        ).join(
            User, Interview.candidate_id == User.id
        ).join(
            JobOffer, Interview.job_offer_id == JobOffer.id
        ).filter(
            Interview.job_offer_id.in_(job_offer_ids),
            Interview.date >= datetime.now(),
            Interview.status == "scheduled"
        ).order_by(
            Interview.date.asc()
        ).limit(limit).all()
        
        # Convert the results to a list of dictionaries
        interviews = []
        for row in results:
            interview = {
                "id": row.id,
                "candidateName": row.candidate_name,
                "jobTitle": row.job_title,
                "date": row.date.strftime("%b %d, %I:%M %p") if row.date else None
            }
            interviews.append(interview)
        
        return interviews
    except Exception as e:
        print(f"Error getting upcoming interviews: {e}")
        return []

def get_interviews_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100):
    """
    Get all interviews for a company's job offers with detailed information
    """
    # Import here to avoid circular imports
    from app.models.user import User
    from app.models.job_offer import JobOffer
    from app.crud.job_offer import get_job_offers_by_company
    
    # Get all job offers for the company
    job_offers = get_job_offers_by_company(db, company_id)
    job_offer_ids = [jo.id for jo in job_offers]
    
    if not job_offer_ids:
        return []
    
    # Query interviews with candidate and job offer details
    results = db.query(
        Interview.id,
        Interview.date,
        Interview.status,
        Interview.job_offer_id,
        User.id.label("candidate_id"),
        User.full_name.label("candidate_name"),
        User.email.label("candidate_email"),
        JobOffer.title.label("job_title")
    ).join(
        User, Interview.candidate_id == User.id
    ).join(
        JobOffer, Interview.job_offer_id == JobOffer.id
    ).filter(
        Interview.job_offer_id.in_(job_offer_ids)
    ).order_by(
        Interview.date.desc()
    ).offset(skip).limit(limit).all()
    
    # Convert the results to a list of dictionaries
    interviews = []
    for row in results:
        interview = {
            "id": row.id,
            "candidateId": row.candidate_id,
            "candidateName": row.candidate_name,
            "candidateEmail": row.candidate_email,
            "jobOfferId": row.job_offer_id,
            "jobTitle": row.job_title,
            "date": row.date.isoformat() if row.date else None,
            "formattedDate": row.date.strftime("%b %d, %Y at %I:%M %p") if row.date else "Not scheduled",
            "status": row.status
        }
        interviews.append(interview)
    
    return interviews