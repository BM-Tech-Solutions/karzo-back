from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.crud import interview as interview_crud
from app.crud import guest_interview as guest_interview_crud
from app.models.company import Company
from app.models.job_offer import JobOffer

router = APIRouter()

@router.put("/interviews/{interview_id}/status", response_model=Dict[str, Any])
def update_interview_status(
    interview_id: int,
    status_data: Dict[str, str],
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Update the status of an interview (works for both regular and guest interviews)
    """
    # First try to find and update a regular interview
    interview = interview_crud.get_interview(db, interview_id=interview_id)
    if interview:
        # Check if this interview belongs to a job offer from this company
        job_offer = db.query(JobOffer).filter(JobOffer.id == interview.job_offer_id).first()
        if not job_offer or job_offer.company_id != current_company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this interview"
            )
        
        # Update the interview status
        updated_interview = interview_crud.update_interview_status(
            db, 
            interview_id=interview_id, 
            status=status_data.get("status")
        )
        
        return {
            "message": "Interview status updated successfully",
            "interview_id": interview_id,
            "status": updated_interview.status
        }
    
    # If not found, try to find and update a guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if guest_interview:
        # Check if this interview belongs to a job offer from this company
        job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
        if not job_offer or job_offer.company_id != current_company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this interview"
            )
        
        # Update the guest interview status
        updated_interview = guest_interview_crud.update_guest_interview_status(
            db, 
            guest_interview_id=interview_id, 
            status=status_data.get("status")
        )
        
        return {
            "message": "Guest interview status updated successfully",
            "interview_id": interview_id,
            "status": updated_interview.status
        }

@router.post("/guest-interviews/{interview_id}/complete", response_model=Dict[str, Any])
def complete_guest_interview(interview_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    # This endpoint doesn't require authentication as it's called from the guest interview flow
    """
    Mark a guest interview as completed with 'processing' status when a guest finishes the interview.
    This endpoint is called from the guest interview room when the interview is completed.
    The status 'processing' allows report generation while indicating the interview is complete.
    """
    # Extract conversation ID from request body
    conversation_id = data.get("conversation_id")
    logger.info(f"Completing guest interview {interview_id} with conversation ID: {conversation_id}")
    
    # Find the guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if not guest_interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest interview with ID {interview_id} not found"
        )
    
    # Update the guest interview with the conversation ID and status
    guest_interview.conversation_id = conversation_id
    db.commit()
    logger.info(f"Updated guest interview {interview_id} with conversation ID: {conversation_id}")
    
    # Update the guest interview status to "processing" to enable report generation
    updated_interview = guest_interview_crud.update_guest_interview_status(
        db, 
        interview_id=interview_id, 
        status="processing"
    )
    
    return {
        "message": "Guest interview marked as completed and ready for report generation",
        "interview_id": interview_id,
        "status": updated_interview.status
    }

@router.post("/guest-interviews/{interview_id}/mark-done", response_model=Dict[str, Any])
def mark_guest_interview_done(interview_id: int, db: Session = Depends(get_db)):
    """
    Mark a guest interview as 'done' after a report has been successfully generated.
    This endpoint should be called after report generation is complete.
    """
    # Find the guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if not guest_interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest interview with ID {interview_id} not found"
        )
    
    # Update the guest interview status to "done"
    updated_interview = guest_interview_crud.update_guest_interview_status(
        db, 
        interview_id=interview_id, 
        status="done"
    )
    
    return {
        "message": "Guest interview marked as done after report generation",
        "interview_id": interview_id,
        "status": updated_interview.status
    }
    
    # If we get here, the interview doesn't exist
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Interview with ID {interview_id} not found"
    )
