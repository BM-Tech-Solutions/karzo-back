from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.interview import Interview, InterviewCreate, InterviewUpdate, InterviewWithDetails
from app.crud import interview as crud
from app.api.auth import get_current_user
from app.schemas.user import User
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=Interview)
def create_interview(
    interview: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Allow both admins and candidates to create interviews
    if current_user.role not in ["admin", "candidate"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create interviews"
        )
    
    # If the user is a candidate, ensure they can only create interviews for themselves
    if current_user.role == "candidate" and interview.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidates can only create interviews for themselves"
        )
    return crud.create_interview(db=db, interview=interview)

@router.get("/{interview_id}", response_model=Interview)
def read_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_interview = crud.get_interview(db, interview_id=interview_id)
    if db_interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Only admin or the candidate can view their interview
    if current_user.role != "admin" and db_interview.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this interview"
        )
    return db_interview

@router.put("/{interview_id}", response_model=Interview)
def update_interview(
    interview_id: int,
    interview: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admins can update interviews
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update interviews"
        )
    
    db_interview = crud.update_interview(db, interview_id=interview_id, interview=interview)
    if db_interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    return db_interview

@router.delete("/{interview_id}")
def delete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admins can delete interviews
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete interviews"
        )
    
    success = crud.delete_interview(db, interview_id=interview_id)
    if not success:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"detail": "Interview deleted successfully"}

# Add a candidate-specific endpoint
@router.get("/candidates/{candidate_id}", response_model=List[InterviewWithDetails])
def read_candidate_interviews(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Log the request for debugging
        logger.info(f"Fetching interviews for candidate ID: {candidate_id}, requested by user ID: {current_user.id}")
        
        # Only admin or the candidate can view their interviews
        if current_user.role != "admin" and current_user.id != candidate_id:
            logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access interviews for candidate {candidate_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these interviews"
            )
        
        # Get interviews with error handling
        try:
            interviews = crud.get_interviews_by_candidate(db, candidate_id=candidate_id)
            logger.info(f"Successfully retrieved {len(interviews)} interviews for candidate {candidate_id}")
            return interviews
        except Exception as e:
            logger.error(f"Error retrieving interviews for candidate {candidate_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving interviews: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in read_candidate_interviews: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

# Add a company-specific endpoint
from app.api.v1.company_auth import get_current_company
from app.models.company import Company

@router.get("/company", response_model=List[dict])
@router.get("/company/", response_model=List[dict])
def read_company_interviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Get all interviews for the current company's job offers
    """
    try:
        logger.info(f"Fetching interviews for company ID: {current_company.id}")
        
        # Get interviews for the company
        interviews = crud.get_interviews_by_company(db, current_company.id, skip, limit)
        
        # Return the interviews (empty list if none found)
        logger.info(f"Successfully retrieved {len(interviews)} interviews for company {current_company.id}")
        return interviews
    except Exception as e:
        logger.error(f"Error retrieving company interviews: {str(e)}", exc_info=True)
        # Return empty list instead of throwing 500 error
        return []