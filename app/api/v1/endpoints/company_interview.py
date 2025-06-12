from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import requests
import os
from datetime import datetime

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.crud import guest_interview as guest_interview_crud
from app.crud import guest_report as guest_report_crud
from app.models.company import Company
from app.models.job_offer import JobOffer

# ElevenLabs API key - in production, this should be in environment variables
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_ea6029e786262953f2b36eeb63ab1d1908470c0e48a2f3d0")

router = APIRouter()

@router.put("/guest-interviews/{interview_id}/status", response_model=Dict[str, Any])
def update_guest_interview_status(
    interview_id: int,
    status_data: Dict[str, str],
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Update the status of a guest interview
    """
    # Find the guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if not guest_interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest interview with ID {interview_id} not found"
        )
    
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
        interview_id=interview_id, 
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

@router.post("/guest-interviews/{interview_id}/generate-report", response_model=Dict[str, Any])
def generate_guest_interview_report(
    interview_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Generate a report for a guest interview by fetching conversation data from ElevenLabs API.
    This endpoint should be called when clicking the "Generate Report" button.
    """
    # Find the guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if not guest_interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest interview with ID {interview_id} not found"
        )
    
    # Check if this interview belongs to a job offer from this company
    job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
    if not job_offer or job_offer.company_id != current_company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate report for this interview"
        )
    
    # Check if conversation_id exists
    if not guest_interview.conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No conversation ID found for this interview"
        )
    
    try:
        # Fetch conversation details from ElevenLabs API
        conversation_data = fetch_elevenlabs_conversation(guest_interview.conversation_id)
        
        if not conversation_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch conversation data from ElevenLabs API"
            )
        
        # Extract relevant data for report
        transcript = conversation_data.get("transcript", [])
        analysis = conversation_data.get("analysis", {})
        metadata = conversation_data.get("metadata", {})
        
        # Create report content
        report_content = {
            "transcript": transcript,
            "summary": analysis.get("transcript_summary", ""),
            "evaluation": analysis.get("evaluation_criteria_results", {}),
            "metadata": {
                "duration": metadata.get("call_duration_secs", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "job_title": job_offer.title
            }
        }
        
        # Create or update report in database
        report = guest_report_crud.create_or_update_guest_report(
            db=db,
            guest_interview_id=interview_id,
            content=report_content
        )
        
        # Update guest interview with report status
        updated_interview = guest_interview_crud.update_guest_interview_report(
            db=db,
            interview_id=interview_id,
            report_id=str(report.id),
            report_status="completed"
        )
        
        # Mark the interview as done
        updated_interview = guest_interview_crud.update_guest_interview_status(
            db=db,
            interview_id=interview_id,
            status="done"
        )
        
        return {
            "message": "Report generated successfully",
            "interview_id": interview_id,
            "report_id": report.id,
            "status": updated_interview.status
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


def fetch_elevenlabs_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch conversation details from ElevenLabs API
    """
    try:
        # Make API request to ElevenLabs
        response = requests.get(
            f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}",
            headers={
                "Xi-Api-Key": ELEVENLABS_API_KEY
            },
            timeout=10  # Add timeout to prevent hanging requests
        )
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching conversation from ElevenLabs: {str(e)}")
        return None