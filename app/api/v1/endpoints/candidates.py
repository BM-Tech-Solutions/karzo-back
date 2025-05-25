from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.user import User, UserCreate, UserUpdate
from app.crud import crud_user
from app.db.session import get_db
import os
import shutil
from uuid import uuid4

router = APIRouter()

@router.get("/", response_model=List[User])
def read_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_user.get_candidates(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=User)
def read_candidate(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_user.get_candidate(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return db_user

@router.post("/", response_model=User)
def create_candidate(user: UserCreate, db: Session = Depends(get_db)):
    # In production, hash the password!
    return crud_user.create_candidate(db, user, hashed_password=user.password)

@router.put("/{user_id}", response_model=User)
def update_candidate(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = crud_user.update_candidate(db, user_id, user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return db_user

@router.delete("/{user_id}", response_model=User)
def delete_candidate(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_user.delete_candidate(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return db_user

@router.post("/{user_id}/update-profile", response_model=User)
async def update_candidate_profile(
    user_id: int, 
    phone: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Update candidate profile with phone and resume"""
    # Check if candidate exists
    db_user = crud_user.get_candidate(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Update fields
    update_data = {}
    
    if phone:
        update_data["phone"] = phone
    
    # Handle resume upload if provided
    if resume:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("app", "uploads", "resumes")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(resume.filename)[1]
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        
        # Store the relative path in the database
        resume_url = f"/uploads/resumes/{unique_filename}"
        update_data["resume_url"] = resume_url
    
    # Update the user in the database
    updated_user = crud_user.update_candidate_profile(db, user_id, update_data)
    
    return updated_user
    