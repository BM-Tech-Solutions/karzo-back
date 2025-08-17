from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from app.db.session import get_db
from app.api.v1.company_auth import get_current_company
from app.crud import invitation as invitation_crud
from app.models.company import Company
from app.models.job_offer import JobOffer
from app.schemas.invitation import InvitationCreate, InvitationUpdate, InvitationRead, InvitationBulkCreate, InvitationPublic

router = APIRouter()

@router.post("/", response_model=Dict[str, Any])
def create_invitation(
    invitation_in: InvitationCreate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Create a new invitation for a candidate.
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    logger.info(f"Received invitation request for email: {invitation_in.email}")
    logger.info(f"Request data: {invitation_in.dict()}")
    
    try:
        # Validate if job_offer_id exists and belongs to the company
        if invitation_in.job_offer_id:
            from app.models.job_offer import JobOffer
            job_offer = db.query(JobOffer).filter(
                JobOffer.id == invitation_in.job_offer_id,
                JobOffer.company_id == current_company.id
            ).first()
            
            if not job_offer:
                logger.error(f"Job offer {invitation_in.job_offer_id} not found or doesn't belong to company {current_company.id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job offer with ID {invitation_in.job_offer_id} not found"
                )
            
            logger.info(f"Job offer validated: {job_offer.title}")
        
        logger.info(f"Creating invitation for {invitation_in.email} from company {current_company.name}")
        invitation = invitation_crud.create_invitation(
            db=db, 
            company_id=current_company.id, 
            invitation_in=invitation_in,
            company_name=current_company.name
        )
        logger.info(f"Invitation created successfully for {invitation_in.email}")
        return invitation
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions as-is
        logger.error(f"HTTP Exception: {http_ex.detail}")
        raise
    except Exception as e:
        logger.error(f"Failed to create invitation: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invitation: {str(e)}"
        )

@router.post("/bulk", response_model=List[Dict[str, Any]])
def create_bulk_invitations(
    bulk_invitation: InvitationBulkCreate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Create multiple invitations at once.
    """
    try:
        invitations = invitation_crud.create_bulk_invitations(
            db=db, 
            company_id=current_company.id, 
            bulk_invitation=bulk_invitation,
            company_name=current_company.name
        )
        return invitations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk invitations: {str(e)}"
        )

@router.get("/", response_model=List[Dict[str, Any]])
def get_company_invitations(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all invitations sent by the current company.
    """
    try:
        invitations = invitation_crud.get_invitations_by_company(db, current_company.id)
        return invitations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve invitations: {str(e)}"
        )

@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invitation(
    invitation_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Delete an invitation.
    """
    # First check if the invitation belongs to the company
    invitation = invitation_crud.get_invitation_by_id(db, invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation.company_id != current_company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this invitation"
        )
    
    success = invitation_crud.delete_invitation(db, invitation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete invitation"
        )
    
    return None

@router.put("/{invitation_id}/resend", response_model=Dict[str, Any])
def resend_invitation(
    invitation_id: int,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """
    Resend an invitation email.
    """
    # First check if the invitation belongs to the company
    invitation = invitation_crud.get_invitation_by_id(db, invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation.company_id != current_company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resend this invitation"
        )
    
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resend invitation with status '{invitation.status}'"
        )
    
    result = invitation_crud.resend_invitation(
        db=db, 
        invitation_id=invitation_id,
        company_name=current_company.name
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation"
        )
    
    return result

@router.get("/token/{token}", response_model=InvitationPublic)
@router.get("/public/{token}", response_model=InvitationPublic)
def get_public_invitation(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Get public invitation details by token (for candidates).
    """
    from app.crud import guest_candidate as guest_candidate_crud
    
    invitation = invitation_crud.get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation is {invitation.status}"
        )
    
    # Add debug logging
    logger = logging.getLogger(__name__)
    now = datetime.now()
    logger.info(f"Checking invitation {invitation.id} expiration: {invitation.expires_at}, current time: {now}")
    
    # Check if candidate already exists
    existing_candidate = guest_candidate_crud.get_guest_candidate_by_email(db, invitation.candidate_email)
    candidate_exists = existing_candidate is not None
    
    logger.info(f"Candidate existence check for {invitation.candidate_email}: {candidate_exists}")
    
    # Get company name
    company = db.query(Company).filter(Company.id == invitation.company_id).first()
    company_name = company.name if company else ""
    
    # Get job title and questions if job_offer_id is provided
    job_title = None
    job_questions = []
    if invitation.job_offer_id:
        job_offer = db.query(JobOffer).filter(JobOffer.id == invitation.job_offer_id).first()
        if job_offer:
            job_title = job_offer.title
            # Get job questions
            job_questions = [q.question for q in job_offer.questions]
    
    # Debug logging for external company fields
    print(f"DEBUG: External company name: {getattr(invitation, 'external_company_name', 'ATTR_NOT_FOUND')}")
    print(f"DEBUG: External company email: {getattr(invitation, 'external_company_email', 'ATTR_NOT_FOUND')}")
    
    return {
        "id": invitation.id,
        "token": invitation.token,
        "company_id": invitation.company_id,
        "company_name": company_name,
        "job_offer_id": invitation.job_offer_id,
        "job_title": job_title,
        "job_questions": job_questions,
        "status": invitation.status,
        "candidate_email": invitation.candidate_email,
        "message": invitation.message,
        "expires_at": invitation.expires_at,
        # Candidate existence check
        "candidate_exists": candidate_exists,
        "existing_candidate": {
            "id": existing_candidate.id,
            "full_name": existing_candidate.full_name,
            "phone": existing_candidate.phone
        } if existing_candidate else None,

        # Language field
        "language": getattr(invitation, 'language', None),
        # TTS parameters
        "tts_temperature": getattr(invitation, 'tts_temperature', None),
        "tts_stability": getattr(invitation, 'tts_stability', None),
        "tts_speed": getattr(invitation, 'tts_speed', None),
        "tts_similarity_boost": getattr(invitation, 'tts_similarity_boost', None),

        # External company fields (with safe attribute access)
        "external_company_name": getattr(invitation, 'external_company_name', None),
        "external_company_email": getattr(invitation, 'external_company_email', None),
        "external_company_size": getattr(invitation, 'external_company_size', None),
        "external_company_sector": getattr(invitation, 'external_company_sector', None),
        "external_company_about": getattr(invitation, 'external_company_about', None),
        "external_company_website": getattr(invitation, 'external_company_website', None)
    }

@router.get("/debug/{token}")
def debug_invitation(token: str, db: Session = Depends(get_db)):
    """
    Debug endpoint to check invitation status and expiration details
    """
    invitation = invitation_crud.get_invitation_by_token(db, token)
    if not invitation:
        return {"status": "not_found", "message": "Invitation not found"}
    
    now = datetime.now()
    days_since_created = (now - invitation.created_at).days
    days_until_expiry = (invitation.expires_at - now).days
    
    return {
        "id": invitation.id,
        "status": invitation.status,
        "created_at": invitation.created_at,
        "expires_at": invitation.expires_at,
        "current_time": now,
        "days_since_created": days_since_created,
        "days_until_expiry": days_until_expiry,
        "candidate_email": invitation.candidate_email
    }
    # This section has been moved to the get_public_invitation function above
