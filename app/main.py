from fastapi import FastAPI
from app.api import auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add this CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])