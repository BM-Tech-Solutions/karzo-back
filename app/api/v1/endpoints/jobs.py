from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.job import Job, JobCreate, JobUpdate
from app.crud import crud_job
from app.db.session import get_db
from app.api.auth import get_current_user, get_current_admin

router = APIRouter()

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
def create_job(job: JobCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    return crud_job.create_job(db, job)

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