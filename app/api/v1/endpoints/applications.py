from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.company import Company
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/submit-with-token", response_model=Dict[str, Any])
async def submit_application_with_token(
    invitation_token: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    cover_letter: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Submit an application using an invitation token
    """
    logger.info(f"Received application submission with token: {invitation_token}")
    
    # Find the invitation by token
    invitation = db.query(Invitation).filter(Invitation.token == invitation_token).first()
    
    if not invitation:
        logger.error(f"Invitation with token {invitation_token} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    # Check if invitation has expired
    if invitation.expires_at < datetime.now():
        logger.error(f"Invitation with token {invitation_token} has expired")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )
    
    # Check if invitation has already been used
    if invitation.status != "pending":
        logger.error(f"Invitation with token {invitation_token} has already been used (status: {invitation.status})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been used"
        )
    
    # Get company information
    company = db.query(Company).filter(Company.id == invitation.company_id).first()
    if not company:
        logger.error(f"Company with ID {invitation.company_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Get job offer information if available
    job_offer = None
    if invitation.job_offer_id:
        job_offer = db.query(JobOffer).filter(JobOffer.id == invitation.job_offer_id).first()
    
    # Handle resume upload if provided
    resume_path = None
    if resume:
        try:
            # Create a unique filename
            file_extension = resume.filename.split('.')[-1]
            unique_filename = f"{invitation_token}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_extension}"
            
            # Ensure uploads directory exists
            import os
            os.makedirs("uploads/resumes", exist_ok=True)
            
            # Save the file
            resume_path = f"uploads/resumes/{unique_filename}"
            with open(resume_path, "wb") as buffer:
                buffer.write(await resume.read())
                
            logger.info(f"Resume saved to {resume_path}")
        except Exception as e:
            logger.error(f"Error saving resume: {str(e)}")
            resume_path = None
    
    try:
        # Create application record
        application = Application(
            name=name,
            email=email,
            phone=phone,
            cover_letter=cover_letter,
            resume_path=resume_path,
            company_id=company.id,
            job_offer_id=invitation.job_offer_id,
            status="pending",
            created_at=datetime.now(),
            invitation_id=invitation.id
        )
        
        # Update invitation status
        invitation.status = "accepted"
        
        # Save to database
        db.add(application)
        db.commit()
        db.refresh(application)
        
        logger.info(f"Application created with ID: {application.id}")
        
        # Return application details
        return {
            "id": application.id,
            "status": "success",
            "message": "Application submitted successfully",
            "company_name": company.name,
            "job_title": job_offer.title if job_offer else None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )
