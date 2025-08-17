from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import requests
import logging
import os
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.crud import guest_interview as guest_interview_crud
from app.crud import guest_report as guest_report_crud
from app.models.company import Company
from app.models.job_offer import JobOffer
from app.utils.openai_helper import generate_report_from_transcript

# ElevenLabs API key - in production, this should be in environment variables
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

router = APIRouter()

class TestGenerateRequest(BaseModel):
    conversation_id: str = Field(..., description="ElevenLabs conversation ID", examples=["conv_3901k1zbg9j3fge8bveptt9nbnpm"])
    elevenlabs_api_key: str = Field(..., description="ElevenLabs XI API key")
    job_title: Optional[str] = Field(None, description="Job title context passed to OpenAI")

class TestReport(BaseModel):
    report_content: str

class TestGenerateResponse(BaseModel):
    message: str
    conversation_id: str
    report: TestReport
    transcript: List[Dict[str, Any]]

@router.post(
    "/test/generate-report",
    response_model=TestGenerateResponse,
    summary="Generate report from ElevenLabs conversation (test)",
    description="Fetches conversation by ID from ElevenLabs and generates a report from the full transcript using OpenAI. Does not persist to DB."
)
def test_generate_report_from_conversation(
    data: TestGenerateRequest = Body(..., example={
        "conversation_id": "conv_3901k1zbg9j3fge8bveptt9nbnpm",
        "elevenlabs_api_key": "sk_xxx",
        "job_title": "Generative AI Engineer"
    })
):
    """Public test endpoint to generate a report directly from an ElevenLabs conversation."""
    conversation_id = data.conversation_id
    xi_api_key = data.elevenlabs_api_key
    job_title = data.job_title

    if not conversation_id or not xi_api_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="conversation_id and elevenlabs_api_key are required")

    try:
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
        # Use standard header casing
        resp = requests.get(url, headers={"Xi-Api-Key": xi_api_key}, timeout=30)
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ElevenLabs error: {resp.status_code}")

        conversation = resp.json()

        # Normalize transcript from various possible shapes
        raw_transcript = conversation.get("transcript")
        normalized: List[Dict[str, Any]] = []

        if isinstance(raw_transcript, list):
            normalized = raw_transcript  # expect list of dicts
        elif isinstance(raw_transcript, str) and raw_transcript.strip():
            normalized = [{"role": "user", "message": raw_transcript.strip()}]
        else:
            # Try alternative keys often used by providers
            alt = conversation.get("messages") or conversation.get("turns") or conversation.get("conversation")
            if isinstance(alt, list):
                normalized = alt
            elif isinstance(alt, str) and alt.strip():
                normalized = [{"role": "user", "message": alt.strip()}]
            else:
                normalized = []

        logger.info(f"Test generate: transcript items = {len(normalized)}")

        # Project to simplified transcript shape {role, message}
        simple_transcript: List[Dict[str, Any]] = []
        for turn in normalized:
            if not isinstance(turn, dict):
                continue
            r = str(turn.get("role", turn.get("speaker", "")) or "").strip()
            m = turn.get("message")
            if m is None:
                # fallbacks for other schemas
                m = turn.get("text") or turn.get("content") or turn.get("value")
            m = str(m or "").strip()
            if not m:
                continue
            simple_transcript.append({"role": r or "user", "message": m})

        # Generate report using simplified transcript
        report = asyncio.run(generate_report_from_transcript(simple_transcript, job_title=job_title))

        return TestGenerateResponse(
            message="Report generated from transcript",
            conversation_id=conversation_id,
            report=TestReport(**report),
            transcript=simple_transcript
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test generate report failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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
    Mark a guest interview as 'report_generated' after a report has been successfully generated.
    This endpoint should be called after report generation is complete.
    """
    # Find the guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if not guest_interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest interview with ID {interview_id} not found"
        )
    
    # Update the guest interview status to "report_generated"
    updated_interview = guest_interview_crud.update_guest_interview_status(
        db, 
        interview_id=interview_id, 
        status="report_generated"
    )
    
    return {
        "message": "Guest interview marked as report_generated after report generation",
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
        
        print(f"ElevenLabs conversation data keys: {list(conversation_data.keys())}")
        print(f"ElevenLabs analysis data: {conversation_data.get('analysis', {})}")
        
        # Extract relevant data for report
        transcript = conversation_data.get("transcript", [])
        analysis = conversation_data.get("analysis", {})
        metadata = conversation_data.get("metadata", {})
        
        print(f"Transcript length: {len(transcript)}")
        print(f"Transcript summary: {analysis.get('transcript_summary', '')}")
        print(f"Analysis keys: {list(analysis.keys())}")
        
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
        
        print(f"Report content summary being sent to OpenAI: {report_content['summary'][:200] if report_content['summary'] else 'EMPTY'}")
        
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
        
        # Mark the interview as report_generated
        updated_interview = guest_interview_crud.update_guest_interview_status(
            db=db,
            interview_id=interview_id,
            status="report_generated"
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


@router.get("/guest-interviews/{interview_id}/summary", response_model=Dict[str, Any])
def get_guest_interview_summary(interview_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Get the candidate summary for a guest interview.
    This endpoint is used by the frontend to fetch the candidate summary for ElevenLabs.
    """
    # Log the request method and headers for debugging
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    try:
        # Convert string ID to integer if needed
        if isinstance(interview_id, str):
            interview_id = int(interview_id)
        
        logger.info(f"Fetching candidate summary for interview ID: {interview_id}")
            
        # Find the guest interview
        guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
        if not guest_interview:
            logger.error(f"Guest interview with ID {interview_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guest interview with ID {interview_id} not found"
            )
        
        # Get the candidate summary from the interview or from the guest candidate
        candidate_summary = guest_interview.candidate_summary
        logger.info(f"Candidate summary from interview: {candidate_summary[:100] if candidate_summary else None}")
        
        # If not found in the interview, try to get it from the guest candidate
        if not candidate_summary and guest_interview.guest_candidate:
            candidate_summary = guest_interview.guest_candidate.candidate_summary
            logger.info(f"Candidate summary from guest candidate: {candidate_summary[:100] if candidate_summary else None}")
        
        response_data = {
            "interview_id": interview_id,
            "candidate_summary": candidate_summary or "No candidate summary available."
        }
        
        logger.info(f"Returning candidate summary response: {response_data['candidate_summary'][:100]}...")
        
        # Create a JSONResponse with explicit CORS headers
        response = JSONResponse(content=response_data)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching candidate summary: {str(e)}")
        error_response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Failed to fetch candidate summary: {str(e)}"}
        )
        error_response.headers["Access-Control-Allow-Origin"] = "*"
        error_response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        error_response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        
        return error_response


@router.options("/guest-interviews/{interview_id}/summary")
def options_guest_interview_summary(interview_id: int):
    """
    Handle OPTIONS requests for the guest interview summary endpoint.
    This is needed for CORS preflight requests.
    """
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours cache for preflight requests
    
    return response


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