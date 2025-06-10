from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.crud import company as company_crud
from app.crud import job_offer as job_offer_crud
from app.crud import interview as interview_crud
from app.crud import candidate as candidate_crud
from app.models.company import Company
from app.schemas.company import CompanyRead, CompanyUpdate
from app.schemas.candidate import CandidateRead

router = APIRouter()

@router.get("/me", response_model=CompanyRead)
def read_company_me(current_company: Company = Depends(get_current_company)):
    """
    Get current company information.
    """
    return current_company

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
        
        # Count total candidates and pending interviews
        total_candidates = 0
        pending_interviews = 0
        
        if job_offer_ids:
            # Only query if there are job offers
            total_candidates = interview_crud.count_unique_candidates_by_job_offers(db, job_offer_ids)
            pending_interviews = interview_crud.count_pending_interviews_by_job_offers(db, job_offer_ids)
        
        return {
            "totalJobOffers": len(job_offers),
            "activeJobOffers": len(active_job_offers),
            "totalCandidates": total_candidates,
            "pendingInterviews": pending_interviews,
        }
    except Exception as e:
        print(f"Error in dashboard stats: {e}")
        return {
            "totalJobOffers": 0,
            "activeJobOffers": 0,
            "totalCandidates": 0,
            "pendingInterviews": 0,
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
        
        if not job_offer_ids:
            return []
        
        # Get candidates who have applied to these job offers
        candidates = candidate_crud.get_candidates_by_job_offers(db, job_offer_ids)
        
        return candidates
    except Exception as e:
        print(f"Error in get company candidates: {e}")
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
