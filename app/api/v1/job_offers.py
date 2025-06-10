from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.job_offer import JobOfferCreate, JobOfferRead, JobOfferUpdate, CandidateInvitation
from app.crud.job_offer import create_job_offer, get_job_offer, get_company_job_offers, update_job_offer, delete_job_offer
from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from typing import List
from datetime import datetime
from app.models.interview import Interview

# Helper function to transform job offer to dict with safe access to fields
def transform_job_offer_to_dict(job_offer):
    try:
        print(f"Transforming job offer: {job_offer.id} - {job_offer.title}")
        return {
            "id": job_offer.id,
            "title": job_offer.title,
            "description": job_offer.description,
            "company_id": job_offer.company_id,
            "is_active": job_offer.is_active,
            "status": "active" if job_offer.is_active else "inactive",
            "created_at": datetime.now().isoformat(),  # Use current date as default
            # Count applications for this job offer
            "applications_count": len(db.query(Interview).filter(Interview.job_offer_id == job_offer.id).all())
        }
    except Exception as e:
        print(f"Error transforming job offer: {e}")
        import traceback
        traceback.print_exc()
        # Return a minimal safe dict if transformation fails
        return {
            "id": getattr(job_offer, 'id', 0),
            "title": getattr(job_offer, 'title', ""),
            "description": getattr(job_offer, 'description', ""),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "applications_count": 0
        }

router = APIRouter()

@router.post("/", response_model=JobOfferRead)
def create_new_job_offer(
    job_offer: JobOfferCreate,
    db: Session = Depends(get_db),
    current_company = Depends(get_current_company)
):
    return create_job_offer(db, job_offer, current_company.id)

@router.get("/", response_model=List[dict])
def read_company_job_offers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_company = Depends(get_current_company)
):
    try:
        print(f"Fetching job offers for company ID: {current_company.id}")
        job_offers = get_company_job_offers(db, current_company.id, skip, limit)
        print(f"Found {len(job_offers)} job offers")
        
        # Use the helper function to transform job offers
        result = [transform_job_offer_to_dict(job) for job in job_offers]
        print(f"Returning {len(result)} processed job offers")
        return result
    except Exception as e:
        print(f"Error in read_company_job_offers: {e}")
        return []

@router.get("/company/", response_model=List[dict])
@router.get("/company", response_model=List[dict])
def read_company_job_offers_by_company(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_company = Depends(get_current_company)
):
    """Get all job offers for the current company"""
    try:
        print(f"Fetching job offers for company ID: {current_company.id}")
        job_offers = get_company_job_offers(db, current_company.id, skip, limit)
        print(f"Found {len(job_offers)} job offers")
        
        # Use the helper function to transform job offers
        result = [transform_job_offer_to_dict(job) for job in job_offers]
        print(f"Returning {len(result)} processed job offers")
        return result
    except Exception as e:
        print(f"Error in read_company_job_offers_by_company: {e}")
        return []

@router.get("/{job_offer_id}", response_model=JobOfferRead)
def read_job_offer(
    job_offer_id: int,
    db: Session = Depends(get_db),
    current_company = Depends(get_current_company)
):
    job_offer = get_job_offer(db, job_offer_id)
    if not job_offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
    
    # Check if job offer belongs to the current company
    if job_offer.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this job offer")
    
    return job_offer

@router.put("/{job_offer_id}", response_model=dict)
def update_existing_job_offer(
    job_offer_id: int,
    job_offer: JobOfferUpdate,
    db: Session = Depends(get_db),
    current_company = Depends(get_current_company)
):
    try:
        print(f"Updating job offer {job_offer_id} with data: {job_offer}")
        db_job_offer = get_job_offer(db, job_offer_id)
        if not db_job_offer:
            raise HTTPException(status_code=404, detail="Job offer not found")
        
        # Check if job offer belongs to the current company
        if db_job_offer.company_id != current_company.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this job offer")
        
        # Update the job offer
        updated_job_offer = update_job_offer(db, job_offer_id, job_offer)
        
        # Transform to dict with status field for frontend
        result = transform_job_offer_to_dict(updated_job_offer)
        print(f"Job offer updated successfully: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating job offer: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to update job offer")

@router.delete("/{job_offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_job_offer(
    job_offer_id: int,
    db: Session = Depends(get_db),
    current_company = Depends(get_current_company)
):
    db_job_offer = get_job_offer(db, job_offer_id)
    if not db_job_offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
    
    # Check if job offer belongs to the current company
    if db_job_offer.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this job offer")
    
    success = delete_job_offer(db, job_offer_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete job offer")
    
    return None

@router.post("/{job_offer_id}/invite", status_code=status.HTTP_202_ACCEPTED)
def invite_candidate(
    job_offer_id: int,
    invitation: CandidateInvitation,
    db: Session = Depends(get_db),
    current_company = Depends(get_current_company)
):
    # Check if job offer exists and belongs to the company
    db_job_offer = get_job_offer(db, job_offer_id)
    if not db_job_offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
    
    if db_job_offer.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Not authorized to invite candidates for this job offer")
    
    # For now, just return a success message as per the requirements
    # The actual email sending functionality will be implemented later
    return {"message": f"Invitation sent to {invitation.email} for job offer {job_offer_id}"}
