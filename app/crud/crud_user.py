from sqlalchemy.orm import Session
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate

def get_candidate(db: Session, user_id: int):
    return db.query(UserModel).filter(UserModel.id == user_id, UserModel.role == "candidate").first()

def get_candidates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserModel).filter(UserModel.role == "candidate").offset(skip).limit(limit).all()

def create_candidate(db: Session, user: UserCreate, hashed_password: str):
    db_user = UserModel(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        resume_url=user.resume_url,
        role="candidate",
        is_active=1,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_candidate(db: Session, user_id: int, user: UserUpdate):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.role == "candidate").first()
    if db_user:
        for key, value in user.dict(exclude_unset=True).items():
            if key == "password" and value:
                db_user.hashed_password = value  # You should hash the password in production
            elif key != "password":
                setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_candidate(db: Session, user_id: int):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.role == "candidate").first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user