"""
Main FastAPI application entry point for Therapy Assistant Agent
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Therapy Assistant Agent API",
    description="AI-powered diagnostic and treatment support for mental health professionals",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Therapy Assistant Agent API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# TODO: Add API routers
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")