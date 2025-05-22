from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user import User, UserCreate, UserUpdate
from app.crud import crud_user
from app.db.session import get_db

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