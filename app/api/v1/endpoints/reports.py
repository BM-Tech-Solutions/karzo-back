from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.report import Report, ReportCreate, ReportUpdate
from app.crud import report as crud
from app.api.auth import get_current_user
from app.schemas.user import User
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=Report)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new report for an interview
    """
    # Only admins or the candidate themselves can create reports
    if current_user.role != "admin" and report.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create reports for other candidates"
        )
    
    # Check if a report already exists for this interview
    existing_report = crud.get_report_by_interview(db, interview_id=report.interview_id)
    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A report already exists for this interview"
        )
    
    return crud.create_report(db=db, report=report)

@router.get("/{report_id}", response_model=Report)
def read_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific report by ID
    """
    db_report = crud.get_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Only admin or the candidate can view their report
    if current_user.role != "admin" and db_report.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    return db_report

@router.put("/{report_id}", response_model=Report)
def update_report(
    report_id: int,
    report: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a report
    """
    # Only admins can update reports
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update reports"
        )
    
    db_report = crud.update_report(db, report_id=report_id, report=report)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a report
    """
    # Only admins can delete reports
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete reports"
        )
    
    success = crud.delete_report(db, report_id=report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"detail": "Report deleted successfully"}

@router.get("/candidates/{candidate_id}", response_model=List[Report])
def read_candidate_reports(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all reports for a specific candidate
    """
    try:
        # Log the request for debugging
        logger.info(f"Fetching reports for candidate ID: {candidate_id}, requested by user ID: {current_user.id}")
        
        # Only admin or the candidate can view their reports
        if current_user.role != "admin" and current_user.id != candidate_id:
            logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access reports for candidate {candidate_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these reports"
            )
        
        # Get reports with error handling
        try:
            reports = crud.get_reports_by_candidate(db, candidate_id=candidate_id)
            logger.info(f"Successfully retrieved {len(reports)} reports for candidate {candidate_id}")
            return reports
        except Exception as e:
            logger.error(f"Error retrieving reports for candidate {candidate_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving reports: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in read_candidate_reports: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/interviews/{interview_id}", response_model=Report)
def read_interview_report(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the report for a specific interview
    """
    db_report = crud.get_report_by_interview(db, interview_id=interview_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found for this interview")
    
    # Only admin or the candidate can view their report
    if current_user.role != "admin" and db_report.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    return db_report
