from fastapi import FastAPI, Request, HTTPException, Depends
from app.api import auth
from app.api.v1.endpoints import candidates, jobs, interviews, reports, transcript_processing
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.session import get_db
from sqlalchemy.orm import Session

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Create a custom CORS middleware class
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            response = JSONResponse(content={})
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours cache for preflight requests
            return response

        # Process the request
        try:
            response = await call_next(request)
            
            # Add CORS headers to every response
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            
            # Create a response for the error
            error_response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )
            
            # Add CORS headers to error responses too
            error_response.headers["Access-Control-Allow-Origin"] = "*"
            error_response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
            error_response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            
            return error_response

# Add our custom CORS middleware
app.add_middleware(CustomCORSMiddleware)

# Handle OPTIONS requests explicitly
@app.options("/{full_path:path}")
async def options_route(full_path: str):
    return {}

# Add exception handler to log errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Add a test endpoint to verify CORS is working
@app.get("/api/test-cors")
async def test_cors():
    return {"message": "CORS is working!"}

# Utility function for authentication
async def authenticate_request(request: Request, db: Session):
    """
    Authenticate a request using the token from the Authorization header.
    
    Args:
        request (Request): The FastAPI request object
        db (Session): The database session
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    token = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
    
    # Import the auth function to get the current user
    from app.api.auth import get_current_user_from_token
    
    # Get the current user from the token
    if not token:
        logger.warning("No token provided in the request")
        raise HTTPException(status_code=401, detail="Not authenticated")
            
    current_user = await get_current_user_from_token(token, db)
    logger.info(f"User authenticated: {current_user.email}, role: {current_user.role}")
    return current_user

# Add direct endpoint for jobs
@app.get("/api/jobs", summary="Get all jobs", description="Retrieve a list of all available jobs with pagination support.")
async def get_jobs_direct(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info(f"Direct GET request to /api/jobs with skip={skip}, limit={limit}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Authenticate the request
        await authenticate_request(request, db)
        
        # Import the CRUD function here to avoid circular imports
        from app.crud.crud_job import get_jobs
        
        # Get the jobs
        jobs = get_jobs(db, skip=skip, limit=limit)
        logger.info(f"Successfully retrieved {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"Error retrieving jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving jobs: {str(e)}"
        )

@app.get("/api/jobs/{job_id}")
async def get_job_direct(job_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info(f"Direct GET request to /api/jobs/{job_id}")
        
        # Import the CRUD function here to avoid circular imports
        from app.crud.crud_job import get_job
        
        job = get_job(db, job_id=job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
            
        logger.info(f"Successfully retrieved job with ID {job_id}")
        return job
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Error retrieving job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job: {str(e)}"
        )

# Add direct endpoint for candidate interviews
@app.get("/api/interviews/candidates/{candidate_id}", 
         summary="Get interviews for a candidate", 
         description="Retrieve all interviews for a specific candidate. Only admins or the candidate themselves can access their interviews.")
async def get_candidate_interviews_direct(candidate_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info(f"Direct GET request to /api/interviews/candidates/{candidate_id}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        try:
            # Authenticate the request
            current_user = await authenticate_request(request, db)
            
            # Check if the user is authorized to access these interviews
            if current_user.role != "admin" and current_user.id != candidate_id:
                logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access interviews for candidate {candidate_id}")
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access these interviews"
                )
            
            # Import the CRUD function here to avoid circular imports
            from app.crud.interview import get_interviews_by_candidate
            
            # Get the interviews
            interviews = get_interviews_by_candidate(db, candidate_id=candidate_id)
            logger.info(f"Successfully retrieved {len(interviews)} interviews for candidate {candidate_id}")
            return interviews
        except HTTPException as he:
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Error retrieving interviews: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving interviews: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in get_candidate_interviews_direct: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

# Add direct endpoint for getting a specific interview
@app.get("/api/interviews/{interview_id}", 
         summary="Get a specific interview", 
         description="Retrieve details for a specific interview by ID. Only admins or the candidate associated with the interview can access it.")
async def get_interview_direct(interview_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info(f"Direct GET request to /api/interviews/{interview_id}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        try:
            # Authenticate the request
            current_user = await authenticate_request(request, db)
            
            # Import the CRUD function here to avoid circular imports
            from app.crud.interview import get_interview
            
            # Get the interview
            interview = get_interview(db, interview_id=interview_id)
            if not interview:
                raise HTTPException(status_code=404, detail="Interview not found")
            
            # Check if the user is authorized to access this interview
            if current_user.role != "admin" and interview.candidate_id != current_user.id:
                logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access interview {interview_id}")
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this interview"
                )
            
            # Convert interview to dictionary for JSON serialization
            interview_dict = {
                "id": interview.id,
                "candidate_id": interview.candidate_id,
                "job_id": interview.job_id,
                "date": interview.date.isoformat() if interview.date else None,
                "status": interview.status,
                # Add other fields as needed
            }
            
            logger.info(f"Successfully retrieved interview {interview_id}")
            return interview_dict
        except HTTPException as he:
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Error retrieving interview: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving interview: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in get_interview_direct: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

# Add direct endpoint for creating an interview
@app.post("/api/interviews/", 
          summary="Create a new interview", 
          description="Create a new interview. Candidates can only create interviews for themselves, while admins can create interviews for any candidate.")
async def create_interview_direct(request: Request, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info("Direct POST request to /api/interviews/")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        try:
            # Authenticate the request
            current_user = await authenticate_request(request, db)
            
            # Parse the request body
            body = await request.json()
            logger.info(f"Request body: {body}")
            
            # Check if the user is authorized to create this interview
            if current_user.role != "admin" and body.get('candidate_id') != current_user.id:
                logger.warning(f"Unauthorized creation attempt: User {current_user.id} tried to create interview for candidate {body.get('candidate_id')}")
                raise HTTPException(
                    status_code=403,
                    detail="Candidates can only create interviews for themselves"
                )
            
            # Import the schemas and CRUD function here to avoid circular imports
            from app.schemas.interview import InterviewCreate
            from app.crud.interview import create_interview
            
            # Create the interview
            interview_data = InterviewCreate(**body)
            interview = create_interview(db, interview=interview_data)
            
            # Convert interview to dictionary for JSON serialization
            interview_dict = {
                "id": interview.id,
                "candidate_id": interview.candidate_id,
                "job_id": interview.job_id,
                "date": interview.date.isoformat() if interview.date else None,
                "status": interview.status,
                # Add other fields as needed
            }
            
            logger.info(f"Successfully created interview with ID {interview.id}")
            return interview_dict
        except HTTPException as he:
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Error creating interview: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error creating interview: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in create_interview_direct: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

# Add direct endpoints for candidates
@app.get("/api/candidates", 
         summary="Get all candidates", 
         description="Retrieve a list of all candidates with pagination support.")
async def get_candidates_direct(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info(f"Direct GET request to /api/candidates with skip={skip}, limit={limit}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Authenticate the request
        current_user = await authenticate_request(request, db)
        
        # Only admins can access the list of all candidates
        if current_user.role != "admin":
            logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access all candidates")
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access all candidates"
            )
        
        # Import the CRUD function here to avoid circular imports
        from app.crud.crud_user import get_candidates
        
        # Get the candidates
        candidates = get_candidates(db, skip=skip, limit=limit)
        logger.info(f"Successfully retrieved {len(candidates)} candidates")
        return candidates
    except Exception as e:
        logger.error(f"Error retrieving candidates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving candidates: {str(e)}"
        )

@app.get("/api/interviews/", 
         summary="Get all interviews", 
         description="Retrieve a list of all interviews. Admin only.")
async def get_all_interviews_direct(request: Request, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info(f"Direct GET request to /api/interviews/")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Authenticate the request
        current_user = await authenticate_request(request, db)
        
        # Only admins can access all interviews
        if current_user.role != "admin":
            logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access all interviews")
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access all interviews"
            )
        
        # Import the CRUD function here to avoid circular imports
        from app.crud.interview import get_all_interviews
        
        # Get all interviews
        interviews = get_all_interviews(db)
        logger.info(f"Successfully retrieved {len(interviews)} interviews")
        return interviews
    except Exception as e:
        logger.error(f"Error retrieving all interviews: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving interviews: {str(e)}"
        )

@app.get("/api/candidates/{candidate_id}", 
         summary="Get a specific candidate", 
         description="Retrieve details for a specific candidate by ID.")
async def get_candidate_direct(candidate_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info(f"Direct GET request to /api/candidates/{candidate_id}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Authenticate the request
        current_user = await authenticate_request(request, db)
        
        # Only admins or the candidate themselves can access their details
        if current_user.role != "admin" and current_user.id != candidate_id:
            logger.warning(f"Unauthorized access attempt: User {current_user.id} tried to access candidate {candidate_id}")
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this candidate"
            )
        
        # Import the CRUD function here to avoid circular imports
        from app.crud.crud_user import get_candidate
        
        # Get the candidate
        candidate = get_candidate(db, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        logger.info(f"Successfully retrieved candidate {candidate_id}")
        return candidate
    except Exception as e:
        logger.error(f"Error retrieving candidate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving candidate: {str(e)}"
        )

# Add direct endpoint for creating an interview
@app.post("/api/interviews/", 
          summary="Create a new interview", 
          description="Create a new interview. Candidates can only create interviews for themselves, while admins can create interviews for any candidate.")
async def create_interview_direct(request: Request, db: Session = Depends(get_db)):
    try:
        # Log the request for debugging
        logger.info("Direct POST request to /api/interviews/")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        try:
            # Authenticate the request
            current_user = await authenticate_request(request, db)
            
            # Parse the request body
            body = await request.json()
            logger.info(f"Request body: {body}")
            
            # Check if the user is authorized to create this interview
            if current_user.role != "admin" and body.get('candidate_id') != current_user.id:
                logger.warning(f"Unauthorized creation attempt: User {current_user.id} tried to create interview for candidate {body.get('candidate_id')}")
                raise HTTPException(
                    status_code=403,
                    detail="Candidates can only create interviews for themselves"
                )
            
            # Import the schemas and CRUD function here to avoid circular imports
            from app.schemas.interview import InterviewCreate
            from app.crud.interview import create_interview
            
            # Create the interview
            interview_data = InterviewCreate(**body)
            interview = create_interview(db, interview=interview_data)
            
            # Convert interview to dictionary for JSON serialization
            interview_dict = {
                "id": interview.id,
                "candidate_id": interview.candidate_id,
                "job_id": interview.job_id,
                "date": interview.date.isoformat() if interview.date else None,
                "status": interview.status,
                # Add other fields as needed
            }
            
            logger.info(f"Successfully created interview with ID {interview.id}")
            return interview_dict
        except HTTPException as he:
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Error creating interview: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error creating interview: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in create_interview_direct: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
# Comment out the jobs router to use our direct endpoints instead
# app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["interviews"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(transcript_processing.router, prefix="/api/transcript", tags=["transcript"])

# Log startup message
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application starting with CORS enabled")
    logger.info("CORS headers will be added to all responses")