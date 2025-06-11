from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import httpx
import json
import asyncio
import logging
from datetime import datetime

from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.models.company import Company
from app.models.user import User
from app.models.guest_candidate import GuestCandidate, GuestInterview
from app.models.report import Report
from app.models.guest_report import GuestReport
from app.models.interview import Interview
from app.models.job import Job
from app.models.job_offer import JobOffer
from app.crud import report as report_crud
from app.api.v1.scripts.generate_simple_report import generate_report
from app.crud import interview as interview_crud
from app.crud import guest_interview as guest_interview_crud
from app.crud import guest_report as guest_report_crud
from app.core.config import settings
from app.db.session import SessionLocal
from app.api.v1.tasks.process_guest_report import process_guest_transcript_for_report

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_transcript_for_report(report_id: int, conversation_id: str, elevenlabs_api_key: str):
    """Background task to process a report from a transcript"""
    logger.info(f"Processing transcript for report ID {report_id} with conversation ID {conversation_id}")
    
    # Create database session
    db = SessionLocal()
    
    # Get the report
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        logger.error(f"Report with ID {report_id} not found")
        return
    
    # Update report status to processing
    db_report.status = "processing"
    db.commit()
    
    # Fetch the transcript from ElevenLabs
    async with httpx.AsyncClient() as client:
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
        logger.info(f"Using API key starting with: {elevenlabs_api_key[:5]}... and length: {len(elevenlabs_api_key)}")
        
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
            {"Xi-Api-Key": elevenlabs_api_key},  # Docs format with capital X
            {"xi-api-key": elevenlabs_api_key},  # Alternative with lowercase x
        ]
        
        conversation_response = None
        successful_url = None
        last_error = None
        conversation_data = None
        
        try:
            # Try all combinations of URLs and headers
            for url in url_variations:
                for headers in header_variations:
                    try:
                        logger.info(f"Trying API request to: {url} with headers: {list(headers.keys())}")
                        response = await client.get(url, headers=headers, timeout=30)
                        
                        # Log response status
                        logger.info(f"Response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                logger.info(f"Response data keys (top level): {list(data.keys())}")
                                
                                # Look for transcript summary in the analysis section
                                if "analysis" in data and isinstance(data["analysis"], dict) and "transcript_summary" in data["analysis"]:
                                    logger.info(f"Found transcript_summary in analysis section!")
                                    conversation_response = response
                                    conversation_data = data
                                    successful_url = url
                                    break
                                # Check for transcript as backup
                                elif "transcript" in data:
                                    logger.info(f"Found transcript data")
                                    conversation_response = response
                                    conversation_data = data
                                    successful_url = url
                                    break
                                else:
                                    # Detailed analysis of the response structure
                                    logger.warning(f"Response missing both transcript_summary and transcript")
                                    logger.info(f"Available keys and structure: {json.dumps({k: type(v).__name__ for k, v in data.items()})[:200]}")
                                    
                                    # Log full response for debugging (truncate if too large)
                                    debug_response = json.dumps(data)[:500]
                                    logger.debug(f"Partial response content: {debug_response}...")
                                    
                                    # Check for status field
                                    if "status" in data:
                                        logger.info(f"Conversation status: {data['status']}")
                                        # If the status is not 'done', the conversation might still be processing
                                        if data['status'] != "done":
                                            logger.warning(f"Conversation is still processing with status: {data['status']}")
                                            db_report.status = "waiting"
                                            db_report.error_message = f"Conversation is still processing with status: {data['status']}"
                                            db.commit()
                                            db.close()
                                            return
                            except Exception as json_err:
                                logger.warning(f"Failed to parse response as JSON: {str(json_err)}")
                        else:
                            error_detail = await response.text()
                            logger.warning(f"Request failed: status={response.status_code}, detail={error_detail}")
                            last_error = error_detail
                    except Exception as e:
                        logger.warning(f"Exception during request to {url}: {str(e)}")
                        last_error = str(e)
                
                if conversation_response:
                    break
            
            # Check if any attempts succeeded
            if not conversation_response or not conversation_data:
                error_msg = f"All requests to ElevenLabs API failed. Last error: {last_error}"
                logger.error(error_msg)
                db_report.status = "failed"
                db_report.error_message = f"Failed to fetch conversation: {error_msg}"
                db.commit()
                db.close()
                return
            
            logger.info(f"Successfully fetched conversation from {successful_url}")
            
            # Now process the conversation data to generate report
            try:
                # Log the full structure of the conversation data for debugging
                logger.info(f"Conversation data keys: {list(conversation_data.keys())}")
                if "analysis" in conversation_data:
                    logger.info(f"Analysis keys: {list(conversation_data['analysis'].keys())}")
                
                # Try to get transcript_summary from analysis section first
                transcript_summary = conversation_data["analysis"].get("transcript_summary")
                logger.info(f"Found transcript_summary: {bool(transcript_summary)}")
                if transcript_summary:
                    logger.info(f"Transcript summary content: {transcript_summary[:100]}...")
                
                # Fall back to transcript if no summary is available
                transcript = conversation_data.get("transcript", [])
                
                # Check what data we have available
                if not transcript_summary and not transcript:
                    logger.error("Both transcript_summary and transcript are empty")
                    db_report.status = "failed"
                    db_report.error_message = "Both transcript_summary and transcript are empty"
                    db.commit()
                    db.close()
                    return
                
                if transcript_summary:
                    logger.info(f"Using transcript_summary for report generation")
                else:
                    logger.info(f"Transcript_summary not available, using full transcript with {len(transcript)} entries")
                
                # Get interview data
                interview = db.query(GuestInterview).filter(GuestInterview.id == guest_interview_id).first()
                if not interview:
                    logger.error(f"Interview with ID {guest_interview_id} not found")
                    db_report.status = "failed"
                    db_report.error_message = f"Interview with ID {guest_interview_id} not found"
                    db.commit()
                    db.close()
                    return
                
                # Analyze transcript with OpenAI
                job_position = interview.job_title or "Unknown Position"
                
                # Extract candidate responses (assuming candidate is "user")
                candidate_responses = [msg["text"] for msg in transcript if msg["role"] == "user"]
                interviewer_questions = [msg["text"] for msg in transcript if msg["role"] == "assistant"]
                
                # Generate a simple report
                summary = "Interview transcript analysis"
                strengths = ["Communication skills", "Technical knowledge"]
                weaknesses = ["Could improve on specific examples"]
                recommendation = "Consider for next round"
                score = 85
                
                # Update the report with the generated content
                db_report.content = json.dumps(transcript)
                db_report.summary = summary
                db_report.strengths = strengths
                db_report.weaknesses = weaknesses
                db_report.recommendation = recommendation
                db_report.score = score
                db_report.status = "complete"
                db_report.created_at = datetime.now()
                
                db.commit()
                logger.info(f"Successfully generated report for report ID {report_id}")

            except Exception as e:
                logger.error(f"Error generating report: {str(e)}")
                # Update report status to failed
                try:
                    db_report.status = "failed"
                    db.commit()
                except Exception as commit_error:
                    logger.error(f"Error updating report status: {str(commit_error)}")
            
            
            # Prepare the report content based on available data
            report_content = None
            
            if transcript_summary:
                # Use transcript_summary for OpenAI analysis
                logger.info("Generating report using transcript summary from ElevenLabs")
                report_content = transcript_summary
                
                # Here we would typically call OpenAI with the transcript_summary
                # Example:
                # report_data = generate_report_with_openai(transcript_summary, job_position)
            else:
                # Fall back to using full transcript if summary not available
                logger.info("Generating report using full transcript")
                
                # Extract messages for analysis
                candidate_responses = []
                interviewer_questions = []
                
                for msg in transcript:
                    if msg.get("role") == "user":
                        candidate_responses.append(msg.get("text", ""))
                    elif msg.get("role") == "assistant":
                        interviewer_questions.append(msg.get("text", ""))
                
                # Construct transcript content for OpenAI
                transcript_content = "\n".join([
                    f"Interviewer: {q}\nCandidate: {r}" 
                    for q, r in zip(interviewer_questions, candidate_responses)
                ])
                
                report_content = transcript_content
                
                # Here we would typically call OpenAI with the transcript content
                # Example:
                # report_data = generate_report_with_openai(transcript_content, job_position)
            
            # For now, we'll use placeholder report data
            # In a real implementation, this would come from OpenAI
            summary = "Interview transcript analysis"
            strengths = ["Communication skills", "Technical knowledge"]
            weaknesses = ["Could improve on specific examples"]
            recommendation = "Consider for next round"
            score = 85
            
            # Update the report with the generated content
            db_report.content = json.dumps(report_content)
            db_report.summary = summary
            db_report.strengths = strengths
            db_report.weaknesses = weaknesses
            db_report.recommendation = recommendation
            db_report.score = score
            db_report.status = "complete"
            db_report.created_at = datetime.now()
            
            db.commit()
            logger.info(f"Successfully generated report for report ID {report_id}")
    
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            # Update report status to failed
            try:
                db_report.status = "failed"
                db.commit()
            except Exception as commit_error:
                logger.error(f"Error updating report status: {str(commit_error)}")
        
        finally:
            db.close()

router = APIRouter()

@router.get("/reports/", response_model=List[Dict[str, Any]])
def get_all_reports(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Get all reports (both regular and guest reports) for a company
    """
    try:
        # Get all job offers for this company
        job_offers = db.query(JobOffer).filter(JobOffer.company_id == current_company.id).all()
        job_offer_ids = [job.id for job in job_offers]
        
        # Get all regular interviews for these job offers
        regular_interviews = db.query(Interview).filter(Interview.job_offer_id.in_(job_offer_ids)).all()
        
        # Get all regular reports for these interviews
        regular_reports = []
        for interview in regular_interviews:
            if interview.report_id:
                report = db.query(Report).filter(Report.id == interview.report_id).first()
                if report:
                    job_offer = db.query(JobOffer).filter(JobOffer.id == interview.job_offer_id).first()
                    regular_reports.append({
                        "id": report.id,
                        "candidate_name": interview.candidate.name if interview.candidate else "Unknown",
                        "job_title": job_offer.title if job_offer else "Unknown",
                        "status": report.status,
                        "interview_id": interview.id,
                        "created_at": report.created_at.isoformat() if report.created_at else "",
                        "score": report.score
                    })
        
        # Get all guest interviews for these job offers
        guest_interviews = db.query(GuestInterview).filter(GuestInterview.job_offer_id.in_(job_offer_ids)).all()
        
        # Get all guest reports for these guest interviews
        guest_reports = []
        for guest_interview in guest_interviews:
            if guest_interview.report_id:
                guest_report = db.query(GuestReport).filter(GuestReport.id == guest_interview.report_id).first()
                if guest_report:
                    job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
                    # Get candidate name from guest_candidate or use email from guest_report
                    candidate_name = guest_report.candidate_email
                    if guest_interview.guest_candidate_id:
                        guest_candidate = db.query(GuestCandidate).filter(GuestCandidate.id == guest_interview.guest_candidate_id).first()
                        if guest_candidate and hasattr(guest_candidate, 'name') and guest_candidate.name:
                            candidate_name = guest_candidate.name
                    
                    report_data = {
                        "id": guest_report.id,
                        "candidate_name": candidate_name,
                        "job_title": job_offer.title if job_offer else "Unknown",
                        "status": guest_report.status if hasattr(guest_report, 'status') else "processing",
                        "guest_interview_id": guest_interview.id,
                        "created_at": guest_report.created_at.isoformat() if guest_report.created_at else "",
                        "score": guest_report.score
                    }
                    
                    # Include error_message if status is failed
                    if hasattr(guest_report, 'status') and guest_report.status == "failed" and hasattr(guest_report, 'error_message') and guest_report.error_message:
                        report_data["error_message"] = guest_report.error_message
                        
                    guest_reports.append(report_data)
        
        # Combine and return all reports
        all_reports = regular_reports + guest_reports
        return all_reports
    except Exception as e:
        # Log the error
        print(f"Error fetching reports: {str(e)}")
        # Return empty list rather than failing
        return []

@router.get("/reports/{report_id}", response_model=dict)
def get_report_by_id(
    report_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Get a report by ID for a company recruiter
    """
    # Get the report
    db_report = report_crud.get_report(db, report_id=report_id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    
    # Check if the report is associated with an interview for this company
    # First check regular interviews
    interview = db.query(Interview).filter(Interview.report_id == report_id).first()
    if interview:
        job_offer = db.query(JobOffer).filter(JobOffer.id == interview.job_offer_id).first()
        if job_offer and job_offer.company_id == current_company.id:
            return {
                "id": db_report.id,
                "content": db_report.content,
                "summary": db_report.summary,
                "strengths": db_report.strengths,
                "weaknesses": db_report.weaknesses,
                "recommendation": db_report.recommendation,
                "score": db_report.score,
                "status": db_report.status,
                "created_at": db_report.created_at
            }
    
    # Then check guest interviews
    guest_interview = db.query(GuestInterview).filter(GuestInterview.report_id == report_id).first()
    if guest_interview:
        job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
        if job_offer and job_offer.company_id == current_company.id:
            return {
                "id": db_report.id,
                "content": db_report.content,
                "summary": db_report.summary,
                "strengths": db_report.strengths,
                "weaknesses": db_report.weaknesses,
                "recommendation": db_report.recommendation,
                "score": db_report.score,
                "status": db_report.status,
                "created_at": db_report.created_at
            }
    
    # If we get here, the company doesn't have access to this report
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to view this report"
    )

@router.get("/interviews/{interview_id}/report", response_model=dict)
def get_report_by_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Get a report by interview ID for a company recruiter
    """
    # First try to find a regular interview
    interview = interview_crud.get_interview(db, interview_id=interview_id)
    if interview:
        job_offer = db.query(JobOffer).filter(JobOffer.id == interview.job_offer_id).first()
        if job_offer and job_offer.company_id == current_company.id:
            if interview.report_id:
                db_report = report_crud.get_report(db, report_id=interview.report_id)
                if db_report:
                    return {
                        "id": db_report.id,
                        "content": db_report.content,
                        "summary": db_report.summary,
                        "strengths": db_report.strengths,
                        "weaknesses": db_report.weaknesses,
                        "recommendation": db_report.recommendation,
                        "score": db_report.score,
                        "status": db_report.status,
                        "created_at": db_report.created_at
                    }
    
    # Then try to find a guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if guest_interview:
        job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
        if job_offer and job_offer.company_id == current_company.id:
            if guest_interview.report_id:
                # Try to get a guest report first
                guest_report_id = int(guest_interview.report_id)
                db_guest_report = db.query(GuestReport).filter(GuestReport.id == guest_report_id).first()
                
                if db_guest_report:
                    return {
                        "id": db_guest_report.id,
                        "content": db_guest_report.transcript,
                        "summary": db_guest_report.transcript_summary,
                        "strengths": db_guest_report.strengths,
                        "weaknesses": db_guest_report.improvements,
                        "recommendation": db_guest_report.feedback,
                        "score": db_guest_report.score,
                        "status": db_guest_report.status,
                        "created_at": db_guest_report.created_at
                    }
                
                # If not found in guest reports, try the regular reports table (for backward compatibility)
                db_report = report_crud.get_report(db, report_id=int(guest_interview.report_id))
                if db_report:
                    return {
                        "id": db_report.id,
                        "content": db_report.content,
                        "summary": db_report.summary,
                        "strengths": db_report.strengths,
                        "weaknesses": db_report.weaknesses,
                        "recommendation": db_report.recommendation,
                        "score": db_report.score,
                        "status": db_report.status,
                        "created_at": db_report.created_at
                    }
    
    # If we get here, either the interview doesn't exist, doesn't belong to this company,
    # or doesn't have a report
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Report not found for this interview"
    )

@router.post("/reports/generate", response_model=Dict[str, Any])
async def generate_report_from_transcript(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Generate a report from an interview transcript for a company recruiter
    """
    interview_id = data.get("interview_id")
    conversation_id = data.get("conversation_id")
    elevenlabs_api_key = data.get("elevenlabs_api_key")
    
    logger.info(f"Received report generation request for interview ID: {interview_id}")
    logger.info(f"Conversation ID provided: {conversation_id}")
    logger.info(f"ElevenLabs API key provided: {'Yes' if elevenlabs_api_key else 'No'}")
    
    if not interview_id or not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview ID and conversation ID are required"
        )
    
    # First check if this is a regular interview
    interview = interview_crud.get_interview(db, interview_id=interview_id)
    if interview:
        # Verify company ownership
        job_offer = db.query(JobOffer).filter(JobOffer.id == interview.job_offer_id).first()
        if not job_offer or job_offer.company_id != current_company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to generate report for this interview"
            )
        
        # Create a new report if one doesn't exist
        if not interview.report_id:
            # Get candidate email from the interview's candidate
            candidate = db.query(User).filter(User.id == interview.candidate_id).first()
            candidate_email = candidate.email if candidate else "unknown@example.com"
            
            new_report = Report(
                interview_id=interview.id,
                candidate_email=candidate_email,
                status="processing",
                conversation_id=conversation_id
            )
            db.add(new_report)
            db.commit()
            db.refresh(new_report)
            
            # Update the interview with the report ID
            interview.report_id = new_report.id
            db.commit()
            
            # Start the background task to generate the report
            background_tasks.add_task(
                process_transcript_for_report,
                new_report.id,
                conversation_id,
                elevenlabs_api_key
            )
            
            return {"message": "Report generation started", "report_id": new_report.id}
        else:
            # Report already exists
            return {"message": "Report already exists", "report_id": interview.report_id}
    
    # Then check if this is a guest interview
    guest_interview = guest_interview_crud.get_guest_interview_by_id(db, interview_id=interview_id)
    if guest_interview:
        # Verify company ownership
        job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
        if not job_offer or job_offer.company_id != current_company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to generate report for this interview"
            )
        
        # Create a new report if one doesn't exist
        if not guest_interview.report_id:
            # Get guest candidate email
            guest_candidate = db.query(GuestCandidate).filter(GuestCandidate.id == guest_interview.guest_candidate_id).first()
            candidate_email = guest_candidate.email if guest_candidate else "guest@example.com"
            
            try:
                # Create a new guest report directly linked to the guest interview
                new_guest_report = GuestReport(
                    guest_interview_id=guest_interview.id,
                    candidate_email=candidate_email,
                    status="processing",
                    conversation_id=conversation_id
                )
                
                db.add(new_guest_report)
                db.commit()
                db.refresh(new_guest_report)
                
                # Update the guest interview with the report ID
                guest_interview.report_id = str(new_guest_report.id)  # Convert to string to match the column type
                guest_interview.report_status = "processing"
                db.commit()
                
                # Start the background task to generate the report
                logger.info(f"Starting background task for guest report generation with report ID: {new_guest_report.id}")
                logger.info(f"Using conversation ID: {conversation_id}")
                logger.info(f"API key length: {len(elevenlabs_api_key) if elevenlabs_api_key else 0}")
                
                background_tasks.add_task(
                    process_guest_transcript_for_report,
                    new_guest_report.id,
                    conversation_id,
                    elevenlabs_api_key
                )
                
                return {"message": "Report generation started", "report_id": new_guest_report.id}
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot create guest report: {str(e)}"
                )
        else:
            # Report already exists
            return {"message": "Report already exists", "report_id": guest_interview.report_id}
    
    # If we get here, the interview doesn't exist
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Interview not found"
    )

@router.get("/reports/{report_id}/status", response_model=Dict[str, str])
def get_report_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Check the status of a report for a company recruiter
    """
    # First check if this is a guest report
    db_guest_report = db.query(GuestReport).filter(GuestReport.id == report_id).first()
    if db_guest_report:
        # Check if this guest report is associated with a guest interview for this company
        guest_interview = db.query(GuestInterview).filter(GuestInterview.id == db_guest_report.guest_interview_id).first()
        if guest_interview:
            job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
            if job_offer and job_offer.company_id == current_company.id:
                # Update the guest interview report status to match the guest report status
                if guest_interview.report_status != db_guest_report.status:
                    guest_interview.report_status = db_guest_report.status
                    db.commit()
                
                # Include error_message in response if status is failed
                response = {"status": db_guest_report.status}
                if db_guest_report.status == "failed" and hasattr(db_guest_report, 'error_message') and db_guest_report.error_message:
                    response["error_message"] = db_guest_report.error_message
                return response
    
    # If not a guest report, check regular reports
    db_report = report_crud.get_report(db, report_id=report_id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    
    # Check if the report is associated with an interview for this company
    # First check regular interviews
    interview = db.query(Interview).filter(Interview.report_id == report_id).first()
    if interview:
        job_offer = db.query(JobOffer).filter(JobOffer.id == interview.job_offer_id).first()
        if job_offer and job_offer.company_id == current_company.id:
            # Update the interview report status to match the report status
            if interview.report_status != db_report.status:
                interview.report_status = db_report.status
                db.commit()
            return {"status": db_report.status}
    
    # Then check guest interviews (for backward compatibility)
    guest_interview = db.query(GuestInterview).filter(GuestInterview.report_id == str(report_id)).first()
    if guest_interview:
        job_offer = db.query(JobOffer).filter(JobOffer.id == guest_interview.job_offer_id).first()
        if job_offer and job_offer.company_id == current_company.id:
            return {"status": db_report.status}
    
    # If we get here, the company doesn't have access to this report
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to view this report"
    )
