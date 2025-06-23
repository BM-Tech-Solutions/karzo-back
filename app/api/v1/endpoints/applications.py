from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid
import os

from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.company import Company
from app.models.guest_candidate import GuestCandidate, GuestInterview
from app.core.config import settings
from app.utils.openai_helper import extract_text_from_cv, generate_candidate_summary

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
    candidate_summary = None
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
            
            # Extract text from CV and generate candidate summary
            try:
                logger.info(f"Extracting text from CV: {resume_path}")
                cv_text = await extract_text_from_cv(resume_path)
                
                if cv_text and len(cv_text) > 100:  # Ensure we have enough text to analyze
                    logger.info(f"Generating candidate summary from CV text")
                    candidate_summary = await generate_candidate_summary(cv_text)
                    logger.info(f"Generated candidate summary: {candidate_summary[:100]}...")
                else:
                    logger.warning(f"Insufficient text extracted from CV: {cv_text[:100]}")
            except Exception as e:
                logger.error(f"Error processing CV for summary: {str(e)}")
                # Continue with application process even if summary generation fails
        except Exception as e:
            logger.error(f"Error saving resume: {str(e)}")
            resume_path = None
    
    try:
        # Check if guest candidate already exists
        guest_candidate = db.query(GuestCandidate).filter(GuestCandidate.email == email).first()
        
        # Create guest candidate if not exists
        if not guest_candidate:
            guest_candidate = GuestCandidate(
                email=email,
                full_name=name,
                phone=phone,
                resume_url=resume_path,
                candidate_summary=candidate_summary,  # Add the candidate summary
                created_at=datetime.now()
            )
            db.add(guest_candidate)
            db.flush()  # Get the guest candidate ID without committing
            logger.info(f"Created new guest candidate with ID: {guest_candidate.id}")
        
        # Create application record
        application = Application(
            name=name,
            email=email,
            phone=phone,
            cover_letter=cover_letter,
            resume_path=resume_path,
            status="pending",
            created_at=datetime.now(),
            company_id=company.id,
            job_offer_id=invitation.job_offer_id,
            invitation_id=invitation.id,
            guest_candidate_id=guest_candidate.id  # Link to guest candidate
        )
        
        # Create guest interview record with status "processing" so report can be generated immediately
        guest_interview = GuestInterview(
            guest_candidate_id=guest_candidate.id,
            job_offer_id=invitation.job_offer_id,
            status="processing",  # Use processing status to enable report generation
            score=0,  # Default score
            created_at=datetime.now(),
            conversation_id=None,  # Will be set when the actual ElevenLabs conversation starts
            report_id=None,
            report_status=None,
            candidate_summary=candidate_summary  # Add the candidate summary for ElevenLabs
        )
        
        # Update invitation status
        invitation.status = "accepted"
        
        # Save to database
        db.add(guest_interview)
        db.add(application)
        db.commit()
        db.refresh(application)
        db.refresh(guest_interview)
        
        logger.info(f"Application created with ID: {application.id}")
        logger.info(f"Interview created with ID: {guest_interview.id}")
        
        # Return application details
        return {
            "id": application.id,
            "guest_interview_id": guest_interview.id,  # Include the guest interview ID
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
