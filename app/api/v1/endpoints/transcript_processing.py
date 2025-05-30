import requests
import logging
import json
import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.db.session import get_db
from app.schemas.report import GenerateReportRequest
from app.crud import report as report_crud
from app.api.auth import get_current_user
from app.schemas.user import User
import openai

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def fetch_transcript_from_elevenlabs(conversation_id: str, api_key: str = None) -> Dict[str, Any]:
    """
    Fetch transcript from ElevenLabs API
    """
    try:
        # Use provided API key or get from environment variable
        if not api_key:
            # Try multiple environment variable names
            api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("NEXT_PUBLIC_ELEVENLABS_API_KEY")
            
            # Hardcoded key for testing (only use in development)
            if not api_key:
                api_key = "sk_7285d9e3401a8364817514d44289c9acad85e3ddeb1e0887"
                logger.warning("Using hardcoded ElevenLabs API key for testing")
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ElevenLabs API key not configured"
            )
        
        logger.info(f"Using ElevenLabs API key: {api_key[:5]}...{api_key[-3:]}")
        
        # Make request to ElevenLabs API
        response = requests.get(
            f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}",
            headers={"Xi-Api-Key": api_key}
        )
        
        # Check if request was successful
        if not response.ok:
            logger.error(f"ElevenLabs API error: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch transcript from ElevenLabs: {response.text}"
            )
        
        # Parse response
        data = response.json()
        
        # Check if conversation is still processing
        if data.get("status") != "done":
            logger.info(f"Conversation {conversation_id} is still processing")
            return {"status": "processing"}
        
        return data
    except Exception as e:
        logger.error(f"Error fetching transcript: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transcript: {str(e)}"
        )

async def analyze_transcript_with_openai(transcript: List[Dict[str, Any]], job_position: str) -> Dict[str, Any]:
    """
    Analyze transcript using OpenAI to generate a report
    """
    try:
        # Format the transcript for OpenAI
        conversation_text = ""
        for turn in transcript:
            role = turn.get("role", "unknown")
            message = turn.get("message", "")
            conversation_text += f"{role.upper()}: {message}\n\n"
        
        # Create prompt for OpenAI
        prompt = f"""
        You are an expert interview analyst. You've been given the transcript of a job interview for a {job_position} position.
        
        Please analyze this interview and provide:
        1. A score from 0-100 based on the candidate's performance
        2. Detailed feedback on the candidate's interview performance
        3. 3-5 key strengths demonstrated in the interview
        4. 3-5 areas for improvement
        
        Here is the interview transcript:
        
        {conversation_text}
        
        Format your response as a JSON object with the following structure:
        {{
            "score": <score>,
            "feedback": "<detailed feedback>",
            "strengths": ["strength1", "strength2", ...],
            "improvements": ["improvement1", "improvement2", ...]
        }}
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "You are an expert interview analyst."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse OpenAI response
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing transcript: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing transcript: {str(e)}"
        )

async def process_report(report_id: int, conversation_id: str, db: Session, elevenlabs_api_key: str = None):
    """
    Background task to process a report
    """
    try:
        # Get the report
        db_report = report_crud.get_report(db, report_id=report_id)
        if not db_report:
            logger.error(f"Report {report_id} not found")
            return
        
        # Get the interview details to extract job position
        interview = db_report.interview
        job_position = interview.job_title if hasattr(interview, 'job_title') else "Unknown Position"
        
        # Fetch transcript from ElevenLabs
        # Use the conversation_id from the report if available
        report_conversation_id = db_report.conversation_id or conversation_id
        elevenlabs_data = await fetch_transcript_from_elevenlabs(report_conversation_id, elevenlabs_api_key)
        
        # Check if conversation is still processing
        if elevenlabs_data.get("status") == "processing":
            logger.info(f"Conversation {conversation_id} is still processing. Will try again later.")
            return
        
        # Extract transcript and summary
        transcript = elevenlabs_data.get("transcript", [])
        transcript_summary = elevenlabs_data.get("analysis", {}).get("transcript_summary", "")
        
        # Update report with transcript data
        report_crud.update_report(
            db, 
            report_id=report_id, 
            report={
                "conversation_id": conversation_id,
                "transcript": transcript,
                "transcript_summary": transcript_summary
            }
        )
        
        # Analyze transcript with OpenAI
        analysis = await analyze_transcript_with_openai(transcript, job_position)
        
        # Update report with analysis
        report_crud.update_report(
            db, 
            report_id=report_id, 
            report={
                "score": analysis.get("score"),
                "feedback": analysis.get("feedback"),
                "strengths": analysis.get("strengths"),
                "improvements": analysis.get("improvements"),
                "status": "complete"
            }
        )
        
        logger.info(f"Successfully processed report {report_id}")
    except Exception as e:
        logger.error(f"Error processing report {report_id}: {str(e)}", exc_info=True)

@router.post("/generate-report")
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a report from an ElevenLabs transcript
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can generate reports"
        )
    
    # Check if report exists
    db_report = report_crud.get_report(db, report_id=request.report_id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {request.report_id} not found"
        )
    
    # Check if report is already complete
    if db_report.status == "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is already complete"
        )
    
    # Update report with conversation ID
    report_crud.update_report(
        db, 
        report_id=request.report_id, 
        report={"conversation_id": request.conversation_id}
    )
    
    # Start background task to process report
    background_tasks.add_task(
        process_report, 
        report_id=request.report_id, 
        conversation_id=request.conversation_id, 
        db=db,
        elevenlabs_api_key=request.elevenlabs_api_key
    )
    
    return {"message": "Report generation started", "report_id": request.report_id}

@router.get("/check-report-status/{report_id}")
async def check_report_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check the status of a report
    """
    # Get the report
    db_report = report_crud.get_report(db, report_id=report_id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    
    # Check if user has permission to view this report
    if current_user.role != "admin" and db_report.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this report"
        )
    
    return {"status": db_report.status}
