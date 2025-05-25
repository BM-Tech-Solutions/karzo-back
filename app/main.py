from fastapi import FastAPI, Request
from app.api import auth
from app.api.v1.endpoints import candidates, jobs
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# IMPORTANT: CORS middleware must be added before any routes
origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
    # Add any other origins you need
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

# Log startup message
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application starting with CORS enabled")
    logger.info(f"Allowed origins: {origins}")