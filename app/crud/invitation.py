from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import secrets
import string
import logging

from app.models.invitation import Invitation
from app.models.company import Company
from app.models.job_offer import JobOffer
from app.schemas.invitation import InvitationCreate, InvitationUpdate, InvitationBulkCreate
from app.utils.email import send_invitation_email
from app.core.config import settings

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token for invitation links"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_invitation_by_id(db: Session, invitation_id: int) -> Optional[Invitation]:
    """Get invitation by ID"""
    return db.query(Invitation).filter(Invitation.id == invitation_id).first()

def get_invitation_by_token(db: Session, token: str) -> Optional[Invitation]:
    """Get invitation by token"""
    return db.query(Invitation).filter(Invitation.token == token).first()

def get_invitations_by_company(db: Session, company_id: int) -> List[Dict[str, Any]]:
    """Get all invitations sent by a company with job title information"""
    invitations = db.query(
        Invitation, 
        JobOffer.title.label("job_title")
    ).outerjoin(
        JobOffer, 
        Invitation.job_offer_id == JobOffer.id
    ).filter(
        Invitation.company_id == company_id
    ).all()
    
    # Convert to dictionaries with formatted dates
    result = []
    for inv, job_title in invitations:
        result.append({
            "id": inv.id,
            "email": inv.email,
            "status": inv.status,
            "created_at": inv.created_at.isoformat(),
            "expires_at": inv.expires_at.isoformat(),
            "job_offer_id": inv.job_offer_id,
            "job_title": job_title,
            "message": inv.message,
            "resend_count": inv.resend_count,
            "last_sent_at": inv.last_sent_at.isoformat() if inv.last_sent_at else None
        })
    
    return result

def create_invitation(
    db: Session, 
    company_id: int, 
    invitation_in: InvitationCreate,
    company_name: str
) -> Dict[str, Any]:
    """Create a new invitation for a candidate"""
    logger = logging.getLogger(__name__)
    logger.info(f"Creating invitation for email: {invitation_in.email}, company_id: {company_id}")
    
    try:
        # Create expiration date (30 days from now to ensure it doesn't expire too soon)
        now = datetime.now()
        expires_at = now + timedelta(days=30)
        
        # Log the creation time and expiration time
        logger.info(f"Creating invitation with current time: {now} and expiration: {expires_at}")
        
        # Generate a secure token for the invitation link
        token = generate_secure_token()
        logger.debug(f"Generated token: {token}")
        
        # Create invitation record
        invitation = Invitation(
            company_id=company_id,
            job_offer_id=invitation_in.job_offer_id,
            email=invitation_in.email,
            candidate_email=invitation_in.email,  # Set candidate_email to match email
            status="pending",
            created_at=now,
            expires_at=expires_at,
            token=token,
            message=invitation_in.message,
            last_sent_at=now
        )
        
        logger.debug(f"Adding invitation to database: {invitation.email}")
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        logger.info(f"Invitation created with ID: {invitation.id}")
        
        # Get job title if job_offer_id is provided
        job_title = None
        if invitation.job_offer_id:
            logger.debug(f"Looking up job title for job_offer_id: {invitation.job_offer_id}")
            job_offer = db.query(JobOffer).filter(JobOffer.id == invitation.job_offer_id).first()
            if job_offer:
                job_title = job_offer.title
                logger.debug(f"Found job title: {job_title}")
            else:
                logger.warning(f"Job offer with ID {invitation.job_offer_id} not found")
        
        # Generate invitation link for application form
        invitation_link = f"{settings.FRONTEND_URL}/invitation/{token}"
        logger.debug(f"Generated application link: {invitation_link}")
        
        # Send invitation email
        logger.info(f"Attempting to send invitation email to: {invitation.email}")
        try:
            email_sent = send_invitation_email(
                email_to=invitation.email,
                company_name=company_name,
                job_title=job_title,
                invitation_link=invitation_link,
                message=invitation.message
            )
            
            if email_sent:
                logger.info(f"Email sent successfully to {invitation.email}")
            else:
                logger.error(f"Failed to send email to {invitation.email}")
        except Exception as email_error:
            logger.error(f"Exception while sending email: {str(email_error)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return {
            "id": invitation.id,
            "email": invitation.email,
            "status": invitation.status,
            "created_at": invitation.created_at.isoformat(),
            "expires_at": invitation.expires_at.isoformat(),
            "job_offer_id": invitation.job_offer_id,
            "job_title": job_title,
            "message": invitation.message,
            "token": token,
            "invitation_link": invitation_link
        }
    except Exception as e:
        logger.error(f"Error creating invitation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def create_bulk_invitations(
    db: Session, 
    company_id: int, 
    bulk_invitation: InvitationBulkCreate,
    company_name: str
) -> List[Dict[str, Any]]:
    """Create multiple invitations at once"""
    now = datetime.now()
    expires_at = now + timedelta(days=30)
    
    # Log the creation time and expiration time
    logger = logging.getLogger(__name__)
    logger.info(f"Creating bulk invitations with current time: {now} and expiration: {expires_at}")
    
    # Get job title if job_offer_id is provided
    job_title = None
    if bulk_invitation.job_offer_id:
        job_offer = db.query(JobOffer).filter(JobOffer.id == bulk_invitation.job_offer_id).first()
        if job_offer:
            job_title = job_offer.title
    
    results = []
    for email in bulk_invitation.emails:
        # Generate a secure token for the invitation link
        token = generate_secure_token()
        
        # Create invitation record
        invitation = Invitation(
            company_id=company_id,
            job_offer_id=bulk_invitation.job_offer_id,
            email=email,
            candidate_email=email,  # Set candidate_email to match email
            status="pending",
            created_at=now,
            expires_at=expires_at,
            token=token,
            message=bulk_invitation.message,
            last_sent_at=now
        )
        
        db.add(invitation)
        
        # Generate invitation link for application form
        invitation_link = f"{settings.FRONTEND_URL}/invitation/{token}"
        
        # Send invitation email
        send_invitation_email(
            email_to=email,
            company_name=company_name,
            job_title=job_title,
            invitation_link=invitation_link,
            message=bulk_invitation.message
        )
        
        results.append({
            "email": email,
            "status": "pending",
            "token": token,
            "invitation_link": invitation_link
        })
    
    db.commit()
    return results

def update_invitation(
    db: Session, 
    invitation_id: int, 
    invitation_update: InvitationUpdate
) -> Optional[Invitation]:
    """Update an invitation's status or message"""
    invitation = get_invitation_by_id(db, invitation_id)
    if not invitation:
        return None
    
    update_data = invitation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invitation, field, value)
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation

def delete_invitation(db: Session, invitation_id: int) -> bool:
    """Delete an invitation"""
    invitation = get_invitation_by_id(db, invitation_id)
    if not invitation:
        return False
    
    db.delete(invitation)
    db.commit()
    return True

def resend_invitation(
    db: Session, 
    invitation_id: int,
    company_name: str
) -> Optional[Dict[str, Any]]:
    """Resend an invitation email"""
    invitation = get_invitation_by_id(db, invitation_id)
    if not invitation:
        return None
    
    # Update resend count and last sent time
    invitation.resend_count += 1
    invitation.last_sent_at = datetime.now()
    
    # Extend expiration date by 7 days from now
    invitation.expires_at = datetime.now() + timedelta(days=7)
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    # Get job title if job_offer_id is provided
    job_title = None
    if invitation.job_offer_id:
        job_offer = db.query(JobOffer).filter(JobOffer.id == invitation.job_offer_id).first()
        if job_offer:
            job_title = job_offer.title
    
    # Generate invitation link
    invitation_link = f"{settings.FRONTEND_URL}/invitation/{invitation.token}"
    
    # Send invitation email
    send_invitation_email(
        email_to=invitation.email,
        company_name=company_name,
        job_title=job_title,
        invitation_link=invitation_link,
        message=invitation.message
    )
    
    return {
        "id": invitation.id,
        "email": invitation.email,
        "status": invitation.status,
        "created_at": invitation.created_at.isoformat(),
        "expires_at": invitation.expires_at.isoformat(),
        "job_offer_id": invitation.job_offer_id,
        "job_title": job_title,
        "resend_count": invitation.resend_count,
        "last_sent_at": invitation.last_sent_at.isoformat()
    }

def check_and_update_expired_invitations(db: Session) -> int:
    """Check for expired invitations and update their status"""
    now = datetime.now()
    expired_invitations = db.query(Invitation).filter(
        and_(
            Invitation.expires_at < now,
            Invitation.status == "pending"
        )
    ).all()
    
    count = 0
    for invitation in expired_invitations:
        invitation.status = "expired"
        db.add(invitation)
        count += 1
    
    if count > 0:
        db.commit()
    
    return count
