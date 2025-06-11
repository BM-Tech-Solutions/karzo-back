import logging
import json
import httpx
import os
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.guest_candidate import GuestInterview
from app.models.guest_report import GuestReport
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def generate_report(report_id: int, conversation_id: str):
    """
    Simple function to generate a report from ElevenLabs transcript_summary:
    1. Fetch transcript_summary from ElevenLabs
    2. Process with OpenAI to generate report
    3. Update the report in the database
    """
    logger.info(f"Starting simple report generation for report ID {report_id}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get the report
        db_report = db.query(GuestReport).filter(GuestReport.id == report_id).first()
        if not db_report:
            logger.error(f"Report with ID {report_id} not found")
            return {"success": False, "message": "Report not found"}
        
        # Update report status to processing
        db_report.status = "processing"
        db.commit()
        
        # Get ElevenLabs API key
        elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("NEXT_PUBLIC_ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            error_msg = "ElevenLabs API key not found"
            logger.error(error_msg)
            update_report_status(db, db_report, "failed", error_msg)
            return {"success": False, "message": error_msg}
            
        # Format conversation ID if needed
        if not conversation_id.startswith("conv_"):
            conversation_id = f"conv_{conversation_id.strip()}"
            
        # Fetch transcript summary
        transcript_data = await fetch_transcript_summary(conversation_id, elevenlabs_api_key)
        if not transcript_data["success"]:
            update_report_status(db, db_report, "failed", transcript_data["message"])
            return transcript_data
            
        transcript_summary = transcript_data["transcript_summary"]
        logger.info(f"Successfully fetched transcript summary (length: {len(transcript_summary)})")
        
        # Get interview data for context
        interview = db.query(GuestInterview).filter(GuestInterview.id == db_report.guest_interview_id).first()
        if not interview:
            error_msg = f"Interview with ID {db_report.guest_interview_id} not found"
            logger.error(error_msg)
            update_report_status(db, db_report, "failed", error_msg)
            return {"success": False, "message": error_msg}
            
        job_title = interview.job_title or "Unknown Position"
        
        # Generate report with OpenAI
        report_data = generate_report_with_openai(transcript_summary, job_title)
        if not report_data["success"]:
            update_report_status(db, db_report, "failed", report_data["message"])
            return report_data
            
        # Update the report with generated content
        db_report.content = json.dumps(transcript_summary)
        db_report.summary = report_data["summary"]
        db_report.strengths = report_data["strengths"]
        db_report.weaknesses = report_data["weaknesses"]
        db_report.recommendation = report_data["recommendation"]
        db_report.score = report_data["score"]
        db_report.status = "complete"
        db_report.created_at = datetime.now()
        
        db.commit()
        logger.info(f"Successfully generated report for report ID {report_id}")
        
        return {"success": True, "message": "Report generated successfully"}
        
    except Exception as e:
        error_msg = f"Error generating report: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        try:
            if 'db_report' in locals():
                update_report_status(db, db_report, "failed", error_msg)
        except Exception:
            pass
            
        return {"success": False, "message": error_msg}
        
    finally:
        db.close()

async def fetch_transcript_summary(conversation_id: str, api_key: str) -> Dict[str, Any]:
    """
    Simplified function to fetch transcript summary from ElevenLabs API
    """
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"Xi-Api-Key": api_key}
    
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching transcript summary from: {url}")
            response = await client.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for transcript_summary in the analysis section
                if "analysis" in data and isinstance(data["analysis"], dict) and "transcript_summary" in data["analysis"]:
                    transcript_summary = data["analysis"]["transcript_summary"]
                    return {"success": True, "transcript_summary": transcript_summary}
                else:
                    error_msg = "Transcript summary not found in response"
                    logger.error(error_msg)
                    return {"success": False, "message": error_msg}
            else:
                error_msg = f"Failed to fetch transcript summary: status={response.status_code}"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}
                
    except Exception as e:
        error_msg = f"Exception while fetching transcript summary: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "message": error_msg}

def generate_report_with_openai(transcript_summary: str, job_title: str) -> Dict[str, Any]:
    """
    Process transcript summary with OpenAI to generate a structured report
    """
    try:
        prompt = f"""
        You are an expert interview analyzer. Analyze this interview transcript summary 
        for a {job_title} position and provide:
        
        1. A brief summary of the interview (3-5 sentences)
        2. 3-5 strengths of the candidate
        3. 2-3 areas for improvement
        4. A specific recommendation (reject, consider, strong consider, or hire)
        5. An overall score from 0-100
        
        Interview transcript summary:
        {transcript_summary}
        
        Format your response as a JSON object with these keys: summary, strengths (array), 
        weaknesses (array), recommendation, and score (integer).
        """
        
        logger.info("Calling OpenAI to analyze transcript summary")
        response = openai_client.chat.completions.create(
            model="gpt-4",  # Use an appropriate model
            messages=[
                {"role": "system", "content": "You are an expert interview analyzer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        report_content = json.loads(response.choices[0].message.content)
        
        # Validate the response structure
        required_keys = ["summary", "strengths", "weaknesses", "recommendation", "score"]
        for key in required_keys:
            if key not in report_content:
                return {
                    "success": False, 
                    "message": f"OpenAI response missing required key: {key}"
                }
        
        # Convert strengths and weaknesses to lists if they aren't already
        if isinstance(report_content["strengths"], str):
            report_content["strengths"] = [report_content["strengths"]]
        if isinstance(report_content["weaknesses"], str):
            report_content["weaknesses"] = [report_content["weaknesses"]]
            
        # Add success flag
        report_content["success"] = True
        
        logger.info(f"Successfully generated report with OpenAI")
        return report_content
        
    except Exception as e:
        error_msg = f"Error generating report with OpenAI: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "message": error_msg}

def update_report_status(db: Session, report: Any, status: str, error_message: Optional[str] = None):
    """Helper function to update report status"""
    try:
        report.status = status
        if error_message:
            report.error_message = error_message
        db.commit()
    except Exception as e:
        logger.error(f"Failed to update report status: {str(e)}")
        # Don't raise, as this is a helper function
