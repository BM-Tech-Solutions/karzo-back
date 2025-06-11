from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.models.company import Company
from app.models.guest_candidate import GuestInterview
from app.models.guest_report import GuestReport
from app.api.v1.scripts.generate_simple_report import generate_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate/{report_id}")
async def generate_simple_report(
    report_id: int,
    conversation_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Generate a report using the simplified approach with ElevenLabs transcript_summary
    
    This endpoint:
    1. Fetches transcript_summary from ElevenLabs using the conversation ID
    2. Processes it with OpenAI to generate a structured interview report
    3. Updates the guest report record in the database
    """
    # Check if report exists and belongs to the company
    db_report = db.query(GuestReport).filter(GuestReport.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if the report belongs to this company's interviews
    interview = db.query(GuestInterview).filter(GuestInterview.id == db_report.guest_interview_id).first()
    if not interview or interview.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this report")
    
    # Update report status to queued and start background task
    db_report.status = "queued"
    db.commit()
    
    # Start background processing
    background_tasks.add_task(generate_report, report_id=report_id, conversation_id=conversation_id)
    
    logger.info(f"Simple report generation started for report ID {report_id}")
    return {"message": "Report generation started", "status": "queued"}
