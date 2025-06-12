# Required Backend Changes for Karzo

This document outlines the necessary backend changes to support the enhanced recruiter dashboard functionality.

## API Endpoints

### 1. Create Missing Endpoint
- Implement `/api/company/candidates/passed` endpoint
- This endpoint should return candidates who have passed interviews and were sent by the requesting recruiter's company
- Example implementation:

```python
@router.get("/candidates/passed", response_model=List[CandidateResponse])
async def get_passed_candidates(
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Get all candidates who passed interviews for the current company"""
    candidates = db.query(Candidate).join(JobOffer).filter(
        JobOffer.company_id == current_user.company_id,
        Candidate.status.in_(["passed", "interviewed"])
    ).all()
    
    return candidates
```

## Database Model Updates

### 1. Interview Model
Add the following fields to the Interview model:
```python
conversation_id = Column(String, nullable=True)  # ID of the conversation for report generation
report_id = Column(String, nullable=True)  # ID of the generated report
report_status = Column(String, nullable=True)  # Status of report generation (null, processing, complete)
created_at = Column(DateTime, default=datetime.utcnow)  # When the interview was created
```

### 2. User Model
Ensure the User model has a name field:
```python
name = Column(String, nullable=True)  # User's full name
```

If the model already has a different field for the name (like `full_name`), update the frontend to use that field instead.

## Database Query Fixes

### Fix in `transform_job_offer_to_dict` Function
The error mentions an undefined `db` variable. This should be fixed by:

1. Either passing the db session as a parameter:
```python
def transform_job_offer_to_dict(job_offer, db):
    # Use db here
```

2. Or using a different approach that doesn't require the db variable.

## Migration Steps

1. Create a new migration file to add the required fields to the Interview model:
```
alembic revision --autogenerate -m "Add report fields to Interview model"
```

2. Run the migration:
```
alembic upgrade head
```

3. Test the new endpoint with:
```
curl -X GET "http://localhost:8000/api/company/candidates/passed" -H "Authorization: Bearer YOUR_TOKEN"
```

## Implementation Priority
1. Fix the database model issues first
2. Create the migration and apply it
3. Implement the missing endpoint
4. Fix any query errors

Once these changes are implemented, the frontend will be able to properly display passed candidates and generate interview reports.
