from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_report(db: Session, report_id: int) -> Optional[Report]:
    """
    Get a report by ID
    """
    return db.query(Report).filter(Report.id == report_id).first()

def get_reports_by_candidate(db: Session, candidate_id: int, skip: int = 0, limit: int = 100) -> List[Report]:
    """
    Get all reports for a specific candidate
    """
    return db.query(Report).filter(Report.candidate_id == candidate_id).offset(skip).limit(limit).all()

def get_report_by_interview(db: Session, interview_id: int) -> Optional[Report]:
    """
    Get a report for a specific interview
    """
    return db.query(Report).filter(Report.interview_id == interview_id).first()

def create_report(db: Session, report: ReportCreate) -> Report:
    """
    Create a new report
    """
    try:
        # Convert strengths and improvements to lists if they're not already
        strengths = report.strengths if report.strengths else []
        improvements = report.improvements if report.improvements else []
        
        db_report = Report(
            interview_id=report.interview_id,
            candidate_id=report.candidate_id,
            score=report.score,
            duration=report.duration,
            feedback=report.feedback,
            strengths=strengths,
            improvements=improvements
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}", exc_info=True)
        db.rollback()
        raise

def update_report(db: Session, report_id: int, report: ReportUpdate) -> Optional[Report]:
    """
    Update a report
    """
    try:
        db_report = get_report(db, report_id)
        if not db_report:
            return None
            
        update_data = report.dict(exclude_unset=True)
        
        # Update the report with the new data
        for key, value in update_data.items():
            setattr(db_report, key, value)
            
        db.commit()
        db.refresh(db_report)
        return db_report
    except Exception as e:
        logger.error(f"Error updating report: {str(e)}", exc_info=True)
        db.rollback()
        raise

def delete_report(db: Session, report_id: int) -> bool:
    """
    Delete a report
    """
    try:
        db_report = get_report(db, report_id)
        if not db_report:
            return False
            
        db.delete(db_report)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}", exc_info=True)
        db.rollback()
        raise
