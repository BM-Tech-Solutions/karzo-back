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