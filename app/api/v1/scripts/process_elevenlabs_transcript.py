#!/usr/bin/env python
import requests
import json
import os
import argparse
import logging
import openai
import sys
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

# Import database models and session
from app.db.session import SessionLocal
from app.models.guest_report import GuestReport
from app.models.guest_candidate import GuestInterview

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_transcript_from_elevenlabs(conversation_id: str, api_key: str) -> Dict[str, Any]:
    """
    Fetch the transcript for a conversation from ElevenLabs API with robust error handling
    """
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
    logger.info(f"Using API key starting with: {api_key[:5]}... and length: {len(api_key)}")
    
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
    successful_url = None
    
    # Try all combinations of URLs and headers
    for url in url_variations:
        for headers in header_variations:
            try:
                logger.info(f"Trying API request to: {url} with headers: {list(headers.keys())}")
                response = requests.get(url, headers=headers, timeout=30)
                response_data = None
                
                # Log response status
                logger.info(f"Response status: {response.status_code}")
                
                try:
                    response_data = response.json()
                    logger.info(f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                except Exception as e:
                    logger.warning(f"Failed to parse response as JSON: {str(e)}")
                    continue
                
                if response.status_code == 200 and response_data and isinstance(response_data, dict) and "transcript" in response_data:
                    logger.info(f"Successful response from URL: {url}")
                    successful_response = response
                    successful_url = url
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
        raise Exception(f"ElevenLabs API error: {error_msg}")
    
    logger.info(f"API request successful with status code: {successful_response.status_code} using URL: {successful_url}")
    
    response = successful_response
    
    # Try parsing the response to verify it's valid JSON
    try:
        data = response.json()
        logger.info(f"Received valid JSON response with keys: {list(data.keys())}")
    except Exception as e:
        logger.error(f"Failed to parse response as JSON: {str(e)}")
        raise Exception(f"Invalid response from ElevenLabs API: {str(e)}")
        
    # Extra validation for expected data structure
    if 'transcript' not in data:
        logger.warning(f"Response does not contain 'transcript' key. Available keys: {list(data.keys())}")
    else:
        logger.info(f"Transcript found with {len(data['transcript'])} entries")
    
    logger.info(f"Successfully received conversation data from ElevenLabs API")
    
    # Check if conversation is still processing
    if data.get("status") != "done":
        logger.info(f"Conversation {conversation_id} is still processing")
        return {"status": "processing"}
    
    return data

def analyze_transcript_with_openai(transcript: List[Dict[str, Any]], job_position: str, openai_api_key: str) -> Dict[str, Any]:
    """
    Analyze transcript using OpenAI to generate a report
    """
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=openai_api_key)
    
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
    
    # Call OpenAI API
    logger.info(f"Sending prompt to OpenAI for job position: {job_position}")
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
    logger.info(f"OpenAI response received")
    analysis = json.loads(analysis_text)
    
    return analysis

def process_transcript_and_generate_report(conversation_id: str, elevenlabs_api_key: str, openai_api_key: str, job_position: str = "AI Engineer") -> Dict[str, Any]:
    """
    Main function to process transcript and generate report
    """
    try:
        # Fetch transcript from ElevenLabs
        conversation_data = fetch_transcript_from_elevenlabs(conversation_id, elevenlabs_api_key)
        
        # Check if conversation is still processing
        if conversation_data.get("status") == "processing":
            return {"status": "processing", "message": "Conversation is still being processed by ElevenLabs"}
        
        # Extract transcript from the response
        transcript = conversation_data.get("transcript", [])
        logger.info(f"Found {len(transcript)} messages in the conversation transcript")
        
        if not transcript:
            error_message = "No transcript data found in conversation response"
            logger.error(error_message)
            return {"status": "failed", "error": error_message}
        
        # Get transcript summary from ElevenLabs if available
        transcript_summary = conversation_data.get("analysis", {}).get("transcript_summary", "")
        
        # Analyze transcript with OpenAI
        analysis = analyze_transcript_with_openai(transcript, job_position, openai_api_key)
        
        # Combine results
        report = {
            "status": "complete",
            "conversation_id": conversation_id,
            "transcript": transcript,
            "transcript_summary": transcript_summary,
            "score": analysis.get("score"),
            "feedback": analysis.get("feedback"),
            "strengths": analysis.get("strengths"),
            "improvements": analysis.get("improvements")
        }
        
        return report
    
    except Exception as e:
        error_message = f"Error processing transcript: {str(e)}"
        logger.error(error_message)
        return {"status": "failed", "error": error_message}

def save_report_to_file(report: Dict[str, Any], output_file: str):
    """
    Save the report to a JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_file}")

def find_existing_report(db: Session, conversation_id: str) -> Optional[GuestReport]:
    """
    Find an existing report by conversation ID
    """
    return db.query(GuestReport).filter(GuestReport.conversation_id == conversation_id).first()

def find_report_by_guest_interview_id(db: Session, guest_interview_id: int) -> Optional[GuestReport]:
    """
    Find an existing report by guest interview ID
    """
    return db.query(GuestReport).filter(GuestReport.guest_interview_id == guest_interview_id).first()

def find_guest_interview_by_conversation_id(db: Session, conversation_id: str) -> Optional[GuestInterview]:
    """
    Find a guest interview by conversation ID
    """
    return db.query(GuestInterview).filter(GuestInterview.conversation_id == conversation_id).first()

def save_report_to_database(report: Dict[str, Any], conversation_id: str, guest_interview_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Save the report to the database - either update an existing report or create a new one
    """
    try:
        # Create a database session
        db = SessionLocal()
        
        # Try to find an existing report by conversation ID
        existing_report = find_existing_report(db, conversation_id)
        
        # If not found by conversation ID but guest_interview_id is provided, try to find by that
        if not existing_report and guest_interview_id:
            existing_report = find_report_by_guest_interview_id(db, guest_interview_id)
        
        # If still not found but we have a conversation ID, try to find the guest interview
        if not existing_report and not guest_interview_id:
            guest_interview = find_guest_interview_by_conversation_id(db, conversation_id)
            if guest_interview:
                # Check if this guest interview already has a report
                existing_report = find_report_by_guest_interview_id(db, guest_interview.id)
                guest_interview_id = guest_interview.id
        
        # Update existing report or create a new one
        if existing_report:
            logger.info(f"Updating existing report with ID {existing_report.id}")
            
            # Update the report fields
            existing_report.transcript = json.dumps(report.get("transcript", []))
            existing_report.transcript_summary = report.get("transcript_summary", "")
            existing_report.score = report.get("score")
            existing_report.feedback = report.get("feedback")
            existing_report.strengths = report.get("strengths", [])
            existing_report.improvements = report.get("improvements", [])
            existing_report.status = "complete"
            existing_report.error_message = None  # Clear any previous error
            
            # Update the guest interview status if available
            if existing_report.guest_interview_id:
                guest_interview = db.query(GuestInterview).filter(GuestInterview.id == existing_report.guest_interview_id).first()
                if guest_interview:
                    guest_interview.report_status = "complete"
            
            db.commit()
            result = {"status": "updated", "report_id": existing_report.id}
        
        elif guest_interview_id:
            # Create a new report
            logger.info(f"Creating new report for guest interview ID {guest_interview_id}")
            
            # Get the guest interview to get the candidate email
            guest_interview = db.query(GuestInterview).filter(GuestInterview.id == guest_interview_id).first()
            if not guest_interview:
                logger.error(f"Guest interview with ID {guest_interview_id} not found")
                return {"status": "error", "message": f"Guest interview with ID {guest_interview_id} not found"}
            
            # Create a new report
            new_report = GuestReport(
                guest_interview_id=guest_interview_id,
                candidate_email=guest_interview.candidate_email,
                conversation_id=conversation_id,
                transcript=json.dumps(report.get("transcript", [])),
                transcript_summary=report.get("transcript_summary", ""),
                score=report.get("score"),
                feedback=report.get("feedback"),
                strengths=report.get("strengths", []),
                improvements=report.get("improvements", []),
                status="complete"
            )
            
            db.add(new_report)
            
            # Update the guest interview status
            guest_interview.report_status = "complete"
            
            db.commit()
            db.refresh(new_report)
            result = {"status": "created", "report_id": new_report.id}
        
        else:
            logger.error("Cannot create report: No guest interview ID provided and no existing report found")
            result = {"status": "error", "message": "Cannot create report: No guest interview ID provided and no existing report found"}
        
        db.close()
        return result
    
    except Exception as e:
        logger.error(f"Error saving report to database: {str(e)}")
        import traceback
        logger.error(f"Detailed error traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description='Process ElevenLabs transcript and generate report')
    parser.add_argument('--conversation-id', required=True, help='ElevenLabs conversation ID')
    parser.add_argument('--guest-interview-id', type=int, help='Guest interview ID (optional)')
    parser.add_argument('--elevenlabs-api-key', help='ElevenLabs API key')
    parser.add_argument('--openai-api-key', help='OpenAI API key')
    parser.add_argument('--job-position', default='AI Engineer', help='Job position for the interview')
    parser.add_argument('--output', default='report.json', help='Output file for the report')
    parser.add_argument('--save-to-db', action='store_true', help='Save the report to the database')
    
    args = parser.parse_args()
    
    # Use provided API keys or get from environment variables
    elevenlabs_api_key = args.elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY") or os.getenv("NEXT_PUBLIC_ELEVENLABS_API_KEY")
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    
    if not elevenlabs_api_key:
        logger.error("ElevenLabs API key not provided")
        return
    
    if not openai_api_key:
        logger.error("OpenAI API key not provided")
        return
    
    # Process transcript and generate report
    report = process_transcript_and_generate_report(
        args.conversation_id,
        elevenlabs_api_key,
        openai_api_key,
        args.job_position
    )
    
    # Save report to file
    save_report_to_file(report, args.output)
    
    # Print report status
    print(f"Report status: {report.get('status')}")
    if report.get('status') == 'complete':
        print(f"Score: {report.get('score')}")
        print(f"Feedback: {report.get('feedback')[:100]}...")
        
        # Save to database if requested
        if args.save_to_db:
            db_result = save_report_to_database(
                report,
                args.conversation_id,
                args.guest_interview_id
            )
            print(f"Database save result: {db_result['status']}")
            if db_result['status'] in ['created', 'updated']:
                print(f"Report ID in database: {db_result['report_id']}")
            elif db_result['status'] == 'error':
                print(f"Error: {db_result['message']}")
    else:
        print(f"Error: {report.get('error', 'Unknown error')}")
        if args.save_to_db:
            print("Not saving to database due to processing error.")
            
    # Return success/failure exit code
    if report.get('status') != 'complete':
        sys.exit(1)

if __name__ == "__main__":
    main()
