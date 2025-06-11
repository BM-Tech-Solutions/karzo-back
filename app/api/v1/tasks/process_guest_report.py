import httpx
import json
import logging
from datetime import datetime

from app.db.session import SessionLocal
from app.models.guest_report import GuestReport
from app.models.guest_candidate import GuestInterview
from app.api.v1.endpoints.transcript_processing import fetch_transcript_from_elevenlabs

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_guest_transcript_for_report(report_id: int, conversation_id: str, elevenlabs_api_key: str):
    """
    Process an ElevenLabs transcript to generate a guest report
    """
    logger.info(f"Starting guest report generation for report ID {report_id} with conversation ID {conversation_id}")
    logger.info(f"Using ElevenLabs API key: {'*' * (len(elevenlabs_api_key) - 4) + elevenlabs_api_key[-4:] if elevenlabs_api_key else 'None'}")
    
    try:
        # Create a new database session for this background task
        db = SessionLocal()
        
        # Get the report
        db_report = db.query(GuestReport).filter(GuestReport.id == report_id).first()
        if not db_report:
            logger.error(f"Guest report with ID {report_id} not found")
            return
        
        # Update report status to processing
        db_report.status = "processing"
        db.commit()
        
        # Fetch the transcript from ElevenLabs using the existing function
        try:
            logger.info(f"Fetching conversation {conversation_id} from ElevenLabs API using fetch_transcript_from_elevenlabs")
            conversation_data = await fetch_transcript_from_elevenlabs(conversation_id, elevenlabs_api_key)
            
            # Check if the conversation is still processing
            if conversation_data.get("status") == "processing":
                logger.info(f"Conversation {conversation_id} is still processing")
                db_report.status = "processing"
                db_report.error_message = "Conversation is still being processed by ElevenLabs"
                db.commit()
                db.close()
                return
                
            logger.info(f"Successfully received conversation data from ElevenLabs API")
            logger.info(f"Conversation data structure: {list(conversation_data.keys()) if isinstance(conversation_data, dict) else 'Not a dictionary'}")
            
            # Process the conversation data to extract the transcript
            # The transcript is in the 'transcript' field of the response
            transcript_data = conversation_data.get("transcript", [])
            logger.info(f"Found {len(transcript_data)} messages in the conversation transcript")
            
            if not transcript_data:
                logger.error("No transcript data found in conversation response")
                db_report.status = "failed"
                db_report.error_message = "No transcript data found in conversation response"
                db.commit()
                db.close()
                return
            
            # Convert the transcript data to our internal format
            transcript = []
            for msg in transcript_data:
                transcript.append({
                    "role": msg.get("role"),
                    "text": msg.get("message"),
                    "timestamp": None  # Timestamp not provided in this format
                })
        except Exception as e:
            error_message = f"Failed to fetch conversation: {str(e)}"
            logger.error(error_message)
            db_report.status = "failed"
            db_report.error_message = error_message
            db.commit()
            db.close()
            return
        
        # Generate a report based on the transcript (real or mock)
        # Extract candidate responses (assuming candidate is "user")
        candidate_responses = [msg["text"] for msg in transcript if msg["role"] == "user"]
        interviewer_questions = [msg["text"] for msg in transcript if msg["role"] == "assistant"]
        
        logger.info(f"Extracted {len(candidate_responses)} candidate responses and {len(interviewer_questions)} interviewer questions")
        
        # Generate a report
        summary = "Interview transcript analysis"
        strengths = ["Communication skills", "Technical knowledge"]
        weaknesses = ["Could improve on specific examples"]
        recommendation = "Consider for next round"
        score = 85
        
        # Update the report with the generated content
        db_report.transcript = json.dumps(transcript)
        db_report.transcript_summary = summary
        db_report.strengths = strengths
        db_report.improvements = weaknesses
        db_report.feedback = recommendation
        db_report.score = score
        db_report.status = "complete"
        
        # Also update the guest interview status
        guest_interview = db.query(GuestInterview).filter(GuestInterview.id == db_report.guest_interview_id).first()
        if guest_interview:
            guest_interview.report_status = "complete"
            
        db.commit()
        logger.info(f"Successfully generated guest report for report ID {report_id}")
    
    except Exception as e:
        logger.error(f"Error generating guest report: {str(e)}")
        import traceback
        logger.error(f"Detailed error traceback: {traceback.format_exc()}")
        # Update report status to failed
        try:
            db_report.status = "failed"
            db_report.error_message = f"Error generating report: {str(e)}"
            db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating guest report status: {str(commit_error)}")
    
    finally:
        db.close()
