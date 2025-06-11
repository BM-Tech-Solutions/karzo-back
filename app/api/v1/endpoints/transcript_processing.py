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
    Fetch transcript from ElevenLabs API with robust handling of different endpoint formats
    """
    try:
        # Use provided API key or get from environment variable
        if not api_key:
            # Try multiple environment variable names
            api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("NEXT_PUBLIC_ELEVENLABS_API_KEY")
            
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ElevenLabs API key not configured"
            )
        
        logger.info(f"Using ElevenLabs API key: {api_key[:5]}...{api_key[-3:]}")
        
        # Clean conversation_id - sometimes they come with prefix/suffix
        conversation_id = conversation_id.strip()
        # Check if we need to format the conversation ID
        if not conversation_id.startswith("conv_"):
            # Try to format it with conv_ prefix if it's not already there
            logger.info(f"Adding 'conv_' prefix to conversation ID: {conversation_id}")
            formatted_conv_id = f"conv_{conversation_id}"
        else:
            formatted_conv_id = conversation_id
        
        logger.info(f"Original conversation_id: {conversation_id}")
        logger.info(f"Formatted conversation_id: {formatted_conv_id}")
        
        # Define all URL variations to try in sequence
        url_variations = [
            # Main format from docs with /convai/
            f"https://api.elevenlabs.io/v1/convai/conversations/{formatted_conv_id}",
            # Alternative without /convai/
            f"https://api.elevenlabs.io/v1/conversations/{formatted_conv_id}",
            # Try with original ID with /convai/
            f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}",
            # Try with original ID without /convai/
            f"https://api.elevenlabs.io/v1/conversations/{conversation_id}"
        ]
        
        # Try different header variations
        header_variations = [
            {"Xi-Api-Key": api_key},  # Docs format with capital X
            {"xi-api-key": api_key},  # Alternative with lowercase x
        ]
        
        successful_response = None
        last_error = None
        
        # Try all combinations of URLs and headers
        for url in url_variations:
            for headers in header_variations:
                try:
                    logger.info(f"Trying API request to: {url} with headers: {headers.keys()}")
                    response = requests.get(url, headers=headers, timeout=30)
                    response_data = None
                    
                    # Log response status
                    logger.info(f"Response status: {response.status_code}")
                    
                    try:
                        response_data = response.json()
                        logger.info(f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                    except Exception as e:
                        logger.warning(f"Failed to parse response as JSON: {str(e)}")
                    
                    if response.status_code == 200 and response_data and isinstance(response_data, dict) and "transcript" in response_data:
                        logger.info(f"Successful response from URL: {url}")
                        successful_response = response
                        break
                    else:
                        error_msg = f"Request failed or invalid response: status={response.status_code}, has_transcript={'transcript' in response_data if response_data and isinstance(response_data, dict) else False}"
                        logger.warning(error_msg)
                        last_error = error_msg
                except Exception as e:
                    logger.warning(f"Exception during request to {url}: {str(e)}")
                    last_error = str(e)
            
            if successful_response:
                break
        
        # Handle the case where no requests were successful
        if not successful_response:
            error_msg = f"All requests to ElevenLabs API failed. Last error: {last_error}"
            logger.error(error_msg)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch transcript from ElevenLabs: {error_msg}"
            )
        
        # Process the successful response
        response = successful_response
        
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
        candidate_responses = 0
        interviewer_questions = 0
        
        for turn in transcript:
            role = turn.get("role", "unknown")
            message = turn.get("message", "")
            conversation_text += f"{role.upper()}: {message}\n\n"
            
            # Count candidate responses and interviewer questions
            if role.lower() == "user" or role.lower() == "candidate":
                candidate_responses += 1
            elif role.lower() == "agent" or role.lower() == "interviewer":
                interviewer_questions += 1
        
        # Check if the transcript is complete enough for analysis
        is_incomplete = candidate_responses < 2 or interviewer_questions < 2
        
        # Log the transcript completeness
        logger.info(f"Transcript analysis: {len(transcript)} turns, {candidate_responses} candidate responses, {interviewer_questions} interviewer questions")
        logger.info(f"Transcript is {'incomplete' if is_incomplete else 'complete enough'} for proper analysis")
        
        # Create prompt for OpenAI
        if is_incomplete:
            # If the transcript is incomplete, instruct OpenAI to provide appropriate feedback
            prompt = f"""
            You are an expert interview analyst. You've been given a transcript of a job interview for a {job_position} position.
            
            IMPORTANT: The transcript appears to be INCOMPLETE. It only contains {len(transcript)} turns with {candidate_responses} candidate responses and {interviewer_questions} interviewer questions.
            
            Based on this incomplete transcript, please provide:
            1. A low score (0-30 out of 100) reflecting the incomplete nature of the transcript
            2. Feedback explaining that the transcript is incomplete and cannot be properly analyzed
            3. No strengths (empty array) since there isn't enough information
            4. One improvement suggestion to complete the interview properly
            
            Here is the incomplete transcript:

            {conversation_text}
            
            Format your response as a JSON object with the following structure:
            {{
                "score": <low_score_out_of_100>,
                "feedback": "The transcript is incomplete and cannot be properly analyzed...",
                "strengths": [],
                "improvements": ["Complete the interview process", ...]
            }}
            """
        else:
            # Normal prompt for complete transcripts
            prompt = f"""
            You are an expert interview analyst. You've been given the transcript of a job interview for a {job_position} position.
            
            Please analyze this interview and provide:
            1. A score from 0-100 (where 100 is perfect) based on the candidate's performance
            2. Detailed feedback on the candidate's interview performance
            3. 3-5 key strengths demonstrated in the interview
            4. 3-5 areas for improvement
            
            Here is the interview transcript:

            {conversation_text}
            
            Format your response as a JSON object with the following structure:
            {{
                "score": <score_out_of_100>,
                "feedback": "<detailed feedback>",
                "strengths": ["strength1", "strength2", ...],
                "improvements": ["improvement1", "improvement2", ...]
            }}
            """
        
        # Log the prompt being sent to OpenAI
        logger.info(f"Sending prompt to OpenAI for job position: {job_position}")
        # Log first 200 chars of transcript to avoid huge logs
        logger.info(f"Transcript preview (first 200 chars): {conversation_text[:200]}...")
        
        # Create a truncated version of the prompt for logging
        truncated_prompt = prompt
        if len(conversation_text) > 500:
            # Replace the full transcript with a truncated version in the log
            transcript_preview = conversation_text[:500] + "...[transcript truncated]"
            truncated_prompt = prompt.replace(conversation_text, transcript_preview)
        
        # Log the actual prompt structure with truncated transcript
        prompt_structure = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are an expert interview analyst."},
                {"role": "user", "content": truncated_prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        logger.info(f"OpenAI request structure: {json.dumps(prompt_structure, indent=2)}")
        
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
        logger.info(f"OpenAI response: {analysis_text}")
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
    logger.info(f"Starting report processing for report_id={report_id}, conversation_id={conversation_id}")
    if elevenlabs_api_key:
        # Log that we're using a provided API key (without showing the actual key)
        logger.info(f"Using ElevenLabs API key: {elevenlabs_api_key[:4]}...{elevenlabs_api_key[-3:]}")
    else:
        logger.info("No ElevenLabs API key provided, will use environment variable")
    try:
        # Get the report
        logger.info(f"Fetching report with id {report_id} from database")
        db_report = report_crud.get_report(db, report_id=report_id)
        if not db_report:
            logger.error(f"Report with id {report_id} not found")
            return
        
        logger.info(f"Found report for interview_id={db_report.interview_id}")
        
        # Get the interview details to extract job position
        interview = db_report.interview
        job_position = interview.job_title if hasattr(interview, 'job_title') else "Unknown Position"
        
        # Fetch transcript from ElevenLabs
        # Use the conversation_id from the report if available
        report_conversation_id = db_report.conversation_id or conversation_id
        logger.info(f"Fetching transcript from ElevenLabs for conversation_id={conversation_id}")
        elevenlabs_data = await fetch_transcript_from_elevenlabs(report_conversation_id, elevenlabs_api_key)
        logger.info(f"Successfully fetched transcript, length: {len(str(elevenlabs_data))} characters")
        
        # Check if conversation is still processing
        if elevenlabs_data.get("status") == "processing":
            logger.info(f"Conversation {conversation_id} is still processing. Will try again later.")
            return
        
        # Extract transcript and summary
        transcript = elevenlabs_data.get("transcript", [])
        transcript_summary = elevenlabs_data.get("analysis", {}).get("transcript_summary", "")
        
        # Update report with transcript data
        logger.info(f"Updating report with transcript data")
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
        logger.info(f"Starting OpenAI analysis for job position: {job_position}")
        analysis = await analyze_transcript_with_openai(transcript, job_position)
        logger.info(f"OpenAI analysis complete, score: {analysis.get('score', 'N/A')}")
        
        # Update report with analysis
        logger.info(f"Updating report with analysis results")
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
        logger.info(f"Setting report status to 'complete'")
        logger.info(f"Report {report_id} successfully updated with analysis results")
        
        logger.info(f"Successfully processed report {report_id}")
    except Exception as e:
        error_message = f"Error processing report {report_id}: {str(e)}"
        logger.error(error_message, exc_info=True)
        
        # Update report status to error with error details
        try:
            logger.info(f"Setting report {report_id} status to 'error'")
            report_crud.update_report(
                db=db,
                report_id=report_id,
                report={
                    "status": "error",
                    "feedback": f"Error generating report: {str(e)}"
                }
            )
            logger.info(f"Report {report_id} marked as error")
        except Exception as update_error:
            logger.error(f"Failed to update report status to error: {str(update_error)}", exc_info=True)

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
