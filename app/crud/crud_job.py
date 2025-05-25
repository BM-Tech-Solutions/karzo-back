from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.schemas.job import JobCreate, JobUpdate
import logging
from datetime import date  # Add this import for date.today()

logger = logging.getLogger(__name__)

def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    jobs = db.query(Job).offset(skip).limit(limit).all()
    
    # Create a list of job dictionaries with requirements as strings
    result = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "posted_date": job.posted_date,
            "requirements": [req.requirement for req in job.requirements]
        }
        result.append(job_dict)
    
    return result

def get_job(db: Session, job_id: int):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        # Create a dictionary with requirements as strings
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "posted_date": job.posted_date,
            "requirements": [req.requirement for req in job.requirements]
        }
        return job_dict
    return None

def create_job(db: Session, job: JobCreate):
    try:
        # Log the job data
        logger.info(f"Creating job with data: {job.dict()}")
        
        # Create the job
        db_job = Job(
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            posted_date=date.today()
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        # Create job requirements
        for req in job.requirements:
            db_requirement = JobRequirement(
                requirement=req,
                job_id=db_job.id
            )
            db.add(db_requirement)
        
        db.commit()
        db.refresh(db_job)
        
        # Return the job with requirements as a list of strings
        return {
            "id": db_job.id,
            "title": db_job.title,
            "company": db_job.company,
            "location": db_job.location,
            "description": db_job.description,
            "posted_date": db_job.posted_date,
            "requirements": [req.requirement for req in db_job.requirements]
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error in create_job: {str(e)}", exc_info=True)
        raise

def update_job(db: Session, job_id: int, job: JobUpdate):
    db_job = get_job(db, job_id)
    if not db_job:
        return None
    
    # Update job fields if provided
    if job.title is not None:
        db_job.title = job.title
    if job.company is not None:
        db_job.company = job.company
    if job.location is not None:
        db_job.location = job.location
    if job.description is not None:
        db_job.description = job.description
    
    # Update requirements if provided
    if job.requirements is not None:
        # Delete existing requirements
        db.query(JobRequirement).filter(JobRequirement.job_id == job_id).delete()
        
        # Add new requirements
        for req_text in job.requirements:
            db_requirement = JobRequirement(requirement=req_text, job_id=job_id)
            db.add(db_requirement)
    
    db.commit()
    db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int):
    db_job = get_job(db, job_id)
    if not db_job:
        return None
    
    db.delete(db_job)
    db.commit()
    return db_job