from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.models.guest_report import GuestReport
from datetime import datetime
import asyncio
from app.utils.openai_helper import generate_report_from_summary

def create_guest_report(
    db: Session,
    guest_interview_id: int,
    candidate_email: str,
    conversation_id: str = None
) -> GuestReport:
    """
    Create a new guest report
    """
    db_report = GuestReport(
        guest_interview_id=guest_interview_id,
        candidate_email=candidate_email,
        status="processing",
        conversation_id=conversation_id,
        created_at=datetime.utcnow()
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_guest_report(db: Session, report_id: int) -> Optional[GuestReport]:
    """
    Get a guest report by ID
    """
    return db.query(GuestReport).filter(GuestReport.id == report_id).first()

def get_guest_report_by_interview_id(db: Session, guest_interview_id: int) -> Optional[GuestReport]:
    """
    Get a guest report by guest interview ID
    """
    return db.query(GuestReport).filter(GuestReport.guest_interview_id == guest_interview_id).first()

def update_guest_report_status(
    db: Session,
    report_id: int,
    status: str
) -> Optional[GuestReport]:
    """
    Update the status of a guest report
    """
    db_report = get_guest_report(db, report_id=report_id)
    if db_report:
        db_report.status = status
        db.commit()
        db.refresh(db_report)
    return db_report

def update_guest_report_content(
    db: Session,
    report_id: int,
    content: Dict[str, Any]
) -> Optional[GuestReport]:
    """
    Update the content of a guest report
    """
    db_report = get_guest_report(db, report_id=report_id)
    if db_report:
        for key, value in content.items():
            if hasattr(db_report, key):
                setattr(db_report, key, value)
        db.commit()
        db.refresh(db_report)
    return db_report


def get_guest_reports_by_company(db: Session, company_id: int) -> List[GuestReport]:
    """
    Get all guest reports for a company by joining with guest_interview and guest_candidate tables
    """
    from app.models.guest_candidate import GuestCandidate, GuestInterview
    from app.models.job_offer import JobOffer
    
    # Query to get all guest reports for interviews associated with the company's job offers
    reports = db.query(GuestReport)\
        .join(GuestInterview, GuestReport.guest_interview_id == GuestInterview.id)\
        .join(JobOffer, GuestInterview.job_offer_id == JobOffer.id)\
        .filter(JobOffer.company_id == company_id)\
        .all()
    
    return reports


def create_or_update_guest_report(
    db: Session,
    guest_interview_id: int,
    content: Dict[str, Any]
) -> GuestReport:
    """
    Create a new guest report or update an existing one for a guest interview
    """
    # Check if a report already exists for this interview
    existing_report = get_guest_report_by_interview_id(db, guest_interview_id=guest_interview_id)
    
    # Extract data from content dictionary
    transcript = content.get("transcript", [])
    summary = content.get("summary", "")
    evaluation = content.get("evaluation", {})
    metadata = content.get("metadata", {})
    
    # Use OpenAI to generate report fields from the summary
    try:
        # Run the async function in a synchronous context
        openai_report = asyncio.run(generate_report_from_summary(summary))
        
        # Extract data from OpenAI response
        report_content = openai_report.get("report_content", "")
        strengths = openai_report.get("strengths", [])
        improvements = openai_report.get("weaknesses", [])
        feedback = openai_report.get("recommendation", "")
        score = openai_report.get("score", 0)
        
        print(f"OpenAI generated report: {openai_report}")
    except Exception as e:
        print(f"Error using OpenAI for report generation: {str(e)}")
        # Fallback to the original logic if OpenAI fails
        score = 0
        if evaluation and isinstance(evaluation, dict):
            # Try to extract scores from evaluation data
            scores = [v.get("score", 0) for v in evaluation.values() if isinstance(v, dict)]
            if scores:
                score = int(sum(scores) / len(scores) * 20)  # Scale to 0-100
        
        # Extract strengths and improvements if available
        strengths = []
        improvements = []
        if isinstance(evaluation, dict):
            for criteria, details in evaluation.items():
                if isinstance(details, dict):
                    if details.get("score", 0) >= 4:  # Consider high scores as strengths
                        strengths.append(f"{criteria}: {details.get('feedback', '')}")
                    elif details.get("score", 0) <= 2:  # Consider low scores as areas for improvement
                        improvements.append(f"{criteria}: {details.get('feedback', '')}")
        
        # Generate feedback from summary
        feedback = summary
    
    if existing_report:
        # Update existing report
        existing_report.transcript = transcript
        existing_report.transcript_summary = summary
        existing_report.report_content = report_content if 'report_content' in locals() else feedback
        existing_report.score = score
        existing_report.feedback = feedback
        existing_report.strengths = strengths
        existing_report.improvements = improvements
        existing_report.status = "completed"
        existing_report.duration = str(metadata.get("duration", 0))
        db.commit()
        db.refresh(existing_report)
        return existing_report
    else:
        # Get interview details to get candidate email
        from app.crud.guest_interview import get_guest_interview_by_id
        interview = get_guest_interview_by_id(db, interview_id=guest_interview_id)
        
        if not interview or not hasattr(interview, 'guest_candidate') or not interview.guest_candidate:
            # If we can't get candidate email, use a placeholder
            candidate_email = "unknown@example.com"
        else:
            candidate_email = interview.guest_candidate.email
        
        # Create new report
        db_report = GuestReport(
            guest_interview_id=guest_interview_id,
            candidate_email=candidate_email,
            conversation_id=interview.conversation_id if interview else None,
            transcript=transcript,
            transcript_summary=summary,
            report_content=report_content if 'report_content' in locals() else feedback,
            score=score,
            feedback=feedback,
            strengths=strengths,
            improvements=improvements,
            duration=str(metadata.get("duration", 0)),
            status="completed",
            created_at=datetime.utcnow()
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report
