from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.schemas.job import Job, JobCreate, JobUpdate
from app.crud import crud_job
from app.db.session import get_db
from app.api.auth import get_current_user, get_current_admin
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Job])
def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_job.get_jobs(db, skip=skip, limit=limit)

@router.get("/{job_id}", response_model=Job)
def read_job(job_id: int, db: Session = Depends(get_db)):
    db_job = crud_job.get_job(db, job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@router.post("/", response_model=Job)
async def create_job(job: JobCreate, request: Request, db: Session = Depends(get_db)):
    try:
        # Log the incoming request data for debugging
        body = await request.json()
        logger.info(f"Received job creation request: {body}")
        
        # Create the job
        return crud_job.create_job(db, job)
    except Exception as e:
        # Log the error
        logger.error(f"Error creating job: {str(e)}", exc_info=True)
        # Re-raise the exception to let FastAPI handle it
        raise

@router.put("/{job_id}", response_model=Job)
def update_job(job_id: int, job: JobUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    db_job = crud_job.update_job(db, job_id, job)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@router.delete("/{job_id}", response_model=Job)
def delete_job(job_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    db_job = crud_job.delete_job(db, job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job