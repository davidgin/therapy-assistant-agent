"""
Main FastAPI application entry point for Therapy Assistant Agent
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import create_tables
from app.services.knowledge_base import initialize_clinical_knowledge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Therapy Assistant Agent API...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    # Initialize clinical knowledge base
    try:
        initialize_clinical_knowledge()
        logger.info("Clinical knowledge base initialized")
    except Exception as e:
        logger.warning(f"Could not initialize knowledge base: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Therapy Assistant Agent API...")

app = FastAPI(
    title="Therapy Assistant Agent API",
    description="AI-powered diagnostic and treatment support for mental health professionals",
    version="0.1.0",
    lifespan=lifespan
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
    return {"status": "healthy", "message": "API is running"}

@app.get("/health/database")
async def database_health():
    """Check database connectivity"""
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}

@app.get("/health/vector-db")
async def vector_db_health():
    """Check vector database status"""
    try:
        from app.services.vector_database import get_vector_db
        vector_db = get_vector_db()
        stats = vector_db.get_stats()
        return {"status": "healthy", "stats": stats}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Vector database error: {str(e)}"}

# TODO: Add API routers
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")