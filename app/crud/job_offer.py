from sqlalchemy.orm import Session
from app.models.job_offer import JobOffer, JobQuestion
from app.models.job_requirement import JobRequirement
from app.schemas.job_offer import JobOfferCreate, JobOfferUpdate
from typing import List, Optional

def get_job_offer(db: Session, job_offer_id: int):
    return db.query(JobOffer).filter(JobOffer.id == job_offer_id).first()

def get_job_offers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(JobOffer).offset(skip).limit(limit).all()

def get_company_job_offers(db: Session, company_id: int, skip: int = 0, limit: int = 100):
    return db.query(JobOffer).filter(JobOffer.company_id == company_id).offset(skip).limit(limit).all()

def get_job_offers_by_company(db: Session, company_id: int):
    """Get all job offers for a specific company without pagination"""
    return db.query(JobOffer).filter(JobOffer.company_id == company_id).all()

def create_job_offer(db: Session, job_offer: JobOfferCreate, company_id: int):
    # Create job offer
    db_job_offer = JobOffer(
        title=job_offer.title,
        description=job_offer.description,
        company_id=company_id
    )
    db.add(db_job_offer)
    db.commit()
    db.refresh(db_job_offer)
    
    # Add requirements
    if job_offer.requirements:
        for req in job_offer.requirements:
            db_requirement = JobRequirement(
                requirement=req,
                job_offer_id=db_job_offer.id
            )
            db.add(db_requirement)
    
    # Add questions
    if job_offer.questions:
        for question in job_offer.questions:
            db_question = JobQuestion(
                question=question,
                job_offer_id=db_job_offer.id
            )
            db.add(db_question)
    
    db.commit()
    db.refresh(db_job_offer)
    return db_job_offer

def update_job_offer(db: Session, job_offer_id: int, job_offer: JobOfferUpdate):
    db_job_offer = get_job_offer(db, job_offer_id)
    if not db_job_offer:
        return None
    
    # Update basic info
    update_data = job_offer.dict(exclude={"requirements", "questions"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job_offer, field, value)
    
    # Update requirements if provided
    if job_offer.requirements is not None:
        # Delete existing requirements
        db.query(JobRequirement).filter(JobRequirement.job_offer_id == job_offer_id).delete()
        
        # Add new requirements
        for req in job_offer.requirements:
            db_requirement = JobRequirement(
                requirement=req,
                job_offer_id=job_offer_id
            )
            db.add(db_requirement)
    
    # Update questions if provided
    if job_offer.questions is not None:
        # Delete existing questions
        db.query(JobQuestion).filter(JobQuestion.job_offer_id == job_offer_id).delete()
        
        # Add new questions
        for question in job_offer.questions:
            db_question = JobQuestion(
                question=question,
                job_offer_id=job_offer_id
            )
            db.add(db_question)
    
    db.commit()
    db.refresh(db_job_offer)
    return db_job_offer

def delete_job_offer(db: Session, job_offer_id: int):
    db_job_offer = get_job_offer(db, job_offer_id)
    if not db_job_offer:
        return False
    
    db.delete(db_job_offer)
    db.commit()
    return True
