from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.crud import company as company_crud
from app.crud import job_offer as job_offer_crud
from app.crud import interview as interview_crud
from app.crud import candidate as candidate_crud
from app.crud import guest_candidate as guest_candidate_crud
from app.crud import guest_interview as guest_interview_crud
from app.crud import guest_report as guest_report_crud
from app.models import guest_report
from app.models.company import Company
from app.models.guest_report import GuestReport
from app.models.guest_candidate import GuestInterview
from app.models.job_offer import JobOffer
from app.crud import company as company_crud
from app.schemas.company import CompanyRead, CompanyUpdate
from app.schemas.candidate import CandidateRead

router = APIRouter()

@router.get("/me", response_model=CompanyRead)
def read_company_me(current_company: Company = Depends(get_current_company)):
    """
    Get current company information.
    """
    return current_company

@router.get("/details", response_model=CompanyRead)
async def get_company_details(
    name: str = Query(..., description="Name of the company to fetch details for"),
    db: Session = Depends(get_db),
):
    """
    Get company details by company name.
    This endpoint is public and doesn't require authentication.
    """
    company = company_crud.get_company_by_name(db, name=name)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company

@router.put("/me", response_model=CompanyRead)
def update_company_me(
    company_in: CompanyUpdate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Update current company information.
    """
    updated_company = company_crud.update_company(db, current_company.id, company_in)
    return updated_company

@router.post("/api-key")
def generate_api_key(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Generate (or rotate) an API key for the authenticated company.
    The key is stored on the company record and returned in the response.
    """
    try:
        api_key = company_crud.generate_and_set_api_key(db, current_company.id)
        return {"api_key": api_key}
    except ValueError:
        raise HTTPException(status_code=404, detail="Company not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

@router.get("/dashboard-stats")
def get_dashboard_stats(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get dashboard statistics for the current company.
    """
    try:
        # Get all job offers for the company
        job_offers = job_offer_crud.get_job_offers_by_company(db, current_company.id)
        
        # Count active job offers
        active_job_offers = [jo for jo in job_offers if jo.is_active]
        
        # Get total candidates (users who have interviews for this company's job offers)
        job_offer_ids = [jo.id for jo in job_offers]
        
        # Count total candidates, pending interviews, and total interviews
        total_candidates = 0
        pending_interviews = 0
        total_interviews = 0
        
        if job_offer_ids:
            # Only query if there are job offers
            total_candidates = interview_crud.count_unique_candidates_by_job_offers(db, job_offer_ids)
            pending_interviews = interview_crud.count_pending_interviews_by_job_offers(db, job_offer_ids)
            
            # Count total interviews (both regular and guest)
            regular_interviews = interview_crud.get_interviews_by_company(db, current_company.id)
            guest_interviews = guest_interview_crud.get_guest_interviews_by_company(db, current_company.id)
            total_interviews = len(regular_interviews) + len(guest_interviews)
        
        return {
            "totalJobOffers": len(job_offers),
            "activeJobOffers": len(active_job_offers),
            "totalCandidates": total_candidates,
            "totalInterviews": total_interviews,
        }
    except Exception as e:
        print(f"Error in dashboard stats: {e}")
        return {
            "totalJobOffers": 0,
            "activeJobOffers": 0,
            "totalCandidates": 0,
            "totalInterviews": 0,
        }

@router.get("/recent-applications")
def get_recent_applications(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
    limit: int = 3
):
    """
    Get recent job applications for the company's job offers.
    """
    try:
        # Get all job offers for the company
        job_offers = job_offer_crud.get_job_offers_by_company(db, current_company.id)
        job_offer_ids = [jo.id for jo in job_offers]
        
        if not job_offer_ids:
            return []
        
        # Get recent applications (interviews) for these job offers
        recent_applications = interview_crud.get_recent_applications_by_job_offers(db, job_offer_ids, limit)
        
        return recent_applications
    except Exception as e:
        print(f"Error in recent applications: {e}")
        return []

@router.get("/upcoming-interviews")
def get_upcoming_interviews(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
    limit: int = 3
):
    """
    Get upcoming interviews for the company's job offers.
    """
    try:
        # Get all job offers for the company
        job_offers = job_offer_crud.get_job_offers_by_company(db, current_company.id)
        job_offer_ids = [jo.id for jo in job_offers]
    
        if not job_offer_ids:
            return []
        
        # Get upcoming interviews for these job offers
        upcoming_interviews = interview_crud.get_upcoming_interviews_by_job_offers(db, job_offer_ids, limit)
        
        return upcoming_interviews
    except Exception as e:
        print(f"Error in upcoming interviews: {e}")
        return []

@router.get("/candidates", response_model=List[dict])
@router.get("/candidates/", response_model=List[dict])
def get_company_candidates(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get all candidates who have applied to this company's job offers.
    """
    try:
        # Get all job offers for the company
        job_offers = job_offer_crud.get_job_offers_by_company(db, current_company.id)
        job_offer_ids = [jo.id for jo in job_offers]
        print(f"Job offer IDs for company {current_company.id}: {job_offer_ids}")
        
        if not job_offer_ids:
            print("No job offers found, returning empty list")
            return []
        
        # Get candidates who have applied to these job offers (both regular and guest)
        candidates = candidate_crud.get_candidates_by_job_offers(db, job_offer_ids)
        print(f"Regular candidates found: {len(candidates)}")
        
        guest_candidates = guest_candidate_crud.get_guest_candidates_by_job_offers(db, job_offer_ids, current_company.id)
        print(f"Guest candidates found: {len(guest_candidates)}")
        if guest_candidates:
            print(f"First guest candidate: {guest_candidates[0]}")
        
        # Combine both types of candidates
        all_candidates = candidates + guest_candidates
        print(f"Total candidates: {len(all_candidates)}")
        
        return all_candidates
    except Exception as e:
        print(f"Error in get company candidates: {e}")
        return []

@router.get("/candidates/passed", response_model=List[dict])
def get_passed_candidates(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get candidates who have passed interviews for this company's job offers.
    """
    try:
        # Get all job offers for the company
        job_offers = job_offer_crud.get_job_offers_by_company(db, current_company.id)
        job_offer_ids = [jo.id for jo in job_offers]
        
        if not job_offer_ids:
            return []
        
        # Get candidates who have passed interviews for these job offers (both regular and guest)
        candidates = candidate_crud.get_passed_candidates_by_job_offers(db, job_offer_ids)
        guest_candidates = guest_candidate_crud.get_passed_guest_candidates_by_job_offers(db, job_offer_ids, current_company.id)
        
        # Combine both types of candidates
        all_passed_candidates = candidates + guest_candidates
        
        return all_passed_candidates
    except Exception as e:
        print(f"Error in get passed candidates: {e}")
        return []

@router.get("/interviews", response_model=List[dict])
@router.get("/interviews/", response_model=List[dict])
def get_company_interviews(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get all interviews for this company's job offers (both regular and guest interviews).
    """
    try:
        # Get regular interviews for this company
        regular_interviews = interview_crud.get_interviews_by_company(db, current_company.id)
        
        # Get guest interviews for this company
        guest_interviews = guest_interview_crud.get_guest_interviews_by_company(db, current_company.id)
        
        # Combine both types of interviews
        all_interviews = regular_interviews + guest_interviews
        
        return all_interviews
    except Exception as e:
        print(f"Error in get company interviews: {e}")
        return []

@router.get("/guest-interviews", response_model=List[dict])
@router.get("/guest-interviews/", response_model=List[dict])
def get_company_guest_interviews(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get all guest interviews for this company's job offers.
    """
    try:
        # Get guest interviews for this company
        guest_interviews = guest_interview_crud.get_guest_interviews_by_company(db, current_company.id)
        
        return guest_interviews
    except Exception as e:
        print(f"Error in get company guest interviews: {e}")
        return []

@router.get("/invitations", response_model=List)
@router.get("/invitations/", response_model=List)
def get_company_invitations(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get all invitations sent by this company.
    """
    try:
        # Get invitations for the company
        invitations = company_crud.get_invitations_by_company(db, current_company.id)
        return invitations
    except Exception as e:
        print(f"Error in get company invitations: {e}")
        # Return empty list instead of throwing 500 error
        return []

@router.post("/invitations")
@router.post("/invitations/")
def create_company_invitation(
    invitation_data: dict,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Create a new invitation for a candidate.
    """
    # Create invitation for the company
    invitation = company_crud.create_invitation(db, current_company.id, invitation_data)
    
    return invitation


@router.get("/reports/")
def get_company_reports(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get all reports for this company's interviews (both regular and guest interviews).
    """
    try:
        # Get all guest reports for this company
        guest_reports = guest_report_crud.get_guest_reports_by_company(db, current_company.id)
        
        # Format the guest reports for the response
        formatted_reports = []
        for report in guest_reports:
            # Get the associated guest interview to get job title and candidate info
            guest_interview = guest_interview_crud.get_guest_interview_by_id(db, report.guest_interview_id)
            
            if guest_interview and guest_interview.guest_candidate and guest_interview.job_offer:
                formatted_reports.append({
                    "id": report.id,
                    "guest_interview_id": report.guest_interview_id,
                    "candidate_name": guest_interview.guest_candidate.full_name,
                    "candidate_email": report.candidate_email,
                    "job_title": guest_interview.job_offer.title,
                    "status": report.status,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                    "duration": report.duration,
                    "conversation_id": report.conversation_id,
                    "error_message": report.error_message,
                    "report_content": getattr(report, "report_content", None)
                })
        
        return formatted_reports
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching reports: {str(e)}"
        )


@router.get("/reports/{report_id}/status")
def get_report_status(
    report_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get the status of a specific report for this company.
    """
    try:
        # Get the report
        report = db.query(guest_report.GuestReport).filter(guest_report.GuestReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID {report_id} not found"
            )
        
        # Check if this report belongs to the company
        guest_interview = guest_interview_crud.get_guest_interview_by_id(db, report.guest_interview_id)
        if not guest_interview or not guest_interview.job_offer or guest_interview.job_offer.company_id != current_company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
        
        # Return the status
        return {
            "status": report.status,
            "error_message": report.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking report status: {str(e)}"
        )


import logging
import traceback

logger = logging.getLogger(__name__)

@router.get("/reports/{report_id}")
def get_report_by_id(
    report_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Get a specific report by ID for this company.
    """
    try:
        logger.info(f"Fetching report with ID: {report_id}")
        
        # Get the report
        report = db.query(guest_report.GuestReport).filter(guest_report.GuestReport.id == report_id).first()
        logger.info(f"Report found: {report is not None}")
        
        if not report:
            logger.warning(f"Report with ID {report_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID {report_id} not found"
            )
        
        # Log report details for debugging
        logger.info(f"Report details: ID={report.id}, status={report.status}, guest_interview_id={report.guest_interview_id}")
        
        # Check if this report belongs to the company
        guest_interview = guest_interview_crud.get_guest_interview_by_id(db, report.guest_interview_id)
        logger.info(f"Guest interview found: {guest_interview is not None}")
        
        if not guest_interview:
            logger.warning(f"Guest interview with ID {report.guest_interview_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guest interview with ID {report.guest_interview_id} not found"
            )
            
        logger.info(f"Guest interview details: ID={guest_interview.id}, job_offer_id={guest_interview.job_offer_id}")
        
        if not guest_interview.job_offer:
            logger.warning(f"Job offer not found for guest interview {guest_interview.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job offer not found for this interview"
            )
            
        logger.info(f"Job offer details: ID={guest_interview.job_offer.id}, company_id={guest_interview.job_offer.company_id}")
        logger.info(f"Current company ID: {current_company.id}")
        
        if guest_interview.job_offer.company_id != current_company.id:
            logger.warning(f"Company ID mismatch: {guest_interview.job_offer.company_id} != {current_company.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
        
        # Get the guest candidate
        guest_candidate = None
        if guest_interview and guest_interview.guest_candidate_id:
            guest_candidate = guest_candidate_crud.get_guest_candidate_by_id(db, guest_interview.guest_candidate_id)
            logger.info(f"Guest candidate found: {guest_candidate is not None}")
            if guest_candidate:
                logger.info(f"Candidate details: ID={guest_candidate.id}, name={guest_candidate.full_name}")
        
        # Format the response
        try:
            response = {
                "id": report.id,
                "content": report.transcript if report.transcript else [],
                "report_content": report.report_content if hasattr(report, 'report_content') and report.report_content else None,
                "language_level": report.language_level if hasattr(report, 'language_level') and report.language_level else "Intermediate",
                "summary": report.transcript_summary if report.transcript_summary else "",
                "strengths": report.strengths if report.strengths else [],
                "weaknesses": report.improvements if report.improvements else [],
                "recommendation": report.feedback if report.feedback else "",
                "score": report.score if report.score else 0,
                "status": report.status,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "candidate_name": guest_candidate.full_name if guest_candidate else "Unknown",
                "job_title": guest_interview.job_offer.title if guest_interview and guest_interview.job_offer else "Unknown",
                "duration": report.duration if report.duration else "0",
                "error_message": report.error_message
            }
            logger.info("Response formatted successfully")
            return response
        except Exception as format_error:
            logger.error(f"Error formatting response: {str(format_error)}")
            logger.error(traceback.format_exc())
            raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_report_by_id: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching report: {str(e)}"
        )

@router.delete("/reports/{report_id}")
def delete_guest_report(
    report_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Delete a guest report and reset the interview status to allow regeneration
    """
    try:
        # Get the report first to verify it exists and belongs to this company
        report = db.query(GuestReport).filter(GuestReport.id == report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get the guest interview to verify company ownership
        guest_interview = db.query(GuestInterview).filter(
            GuestInterview.id == report.guest_interview_id
        ).first()
        
        if not guest_interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated interview not found"
            )
        
        # Get the job offer to verify company ownership
        job_offer = db.query(JobOffer).filter(
            JobOffer.id == guest_interview.job_offer_id
        ).first()
        
        if not job_offer or job_offer.company_id != current_company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this report"
            )
        
        # Delete the report
        db.delete(report)
        
        # Reset the interview status to "passed" so it can be regenerated
        guest_interview.status = "passed"
        guest_interview.report_id = None
        guest_interview.report_status = None
        
        db.commit()
        
        logger.info(f"Deleted guest report {report_id} and reset interview {guest_interview.id} status to 'passed'")
        
        return {
            "message": "Report deleted successfully",
            "report_id": report_id,
            "interview_id": guest_interview.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting guest report {report_id}: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting report: {str(e)}"
        )
