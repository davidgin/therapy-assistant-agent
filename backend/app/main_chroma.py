"""
FastAPI application with ChromaDB vector database (lightweight alternative to FAISS)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import create_tables
from app.services.knowledge_base_chroma import initialize_chroma_clinical_knowledge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Therapy Assistant Agent API with ChromaDB...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    # Initialize ChromaDB clinical knowledge base
    try:
        initialize_chroma_clinical_knowledge()
        logger.info("ChromaDB clinical knowledge base initialized")
    except Exception as e:
        logger.warning(f"Could not initialize ChromaDB knowledge base: {e}")
    
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
    allow_origins=["http://localhost:3000", "http://frontend:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Therapy Assistant Agent API with ChromaDB", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running with ChromaDB"}

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
    """Check ChromaDB status"""
    try:
        from app.services.vector_database_chroma import get_chroma_db
        chroma_db = get_chroma_db()
        stats = chroma_db.get_stats()
        return {"status": "healthy", "stats": stats}
    except Exception as e:
        return {"status": "unhealthy", "message": f"ChromaDB error: {str(e)}"}

@app.get("/api/v1/synthetic-cases")
async def get_synthetic_cases():
    """Get synthetic clinical cases"""
    try:
        import json
        import os
        
        # Load synthetic cases
        data_file = "data/synthetic/synthetic_clinical_cases.json"
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                cases = json.load(f)
            
            # Return first 5 cases for demo
            sample_cases = cases[:5]
            
            return {
                "status": "success",
                "total_cases": len(cases),
                "sample_cases": len(sample_cases),
                "cases": sample_cases
            }
        else:
            return {"status": "error", "message": "Synthetic data file not found"}
            
    except Exception as e:
        return {"status": "error", "message": f"Error loading synthetic cases: {str(e)}"}

@app.get("/api/v1/disorders")
async def get_supported_disorders():
    """Get list of supported disorders"""
    disorders = [
        {
            "name": "Major Depressive Disorder",
            "code": "296.2x",
            "icd11_code": "6A70.1",
            "category": "Depressive Disorders"
        },
        {
            "name": "Generalized Anxiety Disorder", 
            "code": "300.02",
            "icd11_code": "6B00",
            "category": "Anxiety Disorders"
        },
        {
            "name": "Post-Traumatic Stress Disorder",
            "code": "309.81", 
            "icd11_code": "6B40",
            "category": "Trauma and Stressor-Related Disorders"
        },
        {
            "name": "Bipolar I Disorder",
            "code": "296.4x",
            "icd11_code": "6A60", 
            "category": "Bipolar and Related Disorders"
        },
        {
            "name": "ADHD",
            "code": "314.0x",
            "icd11_code": "6A05",
            "category": "Neurodevelopmental Disorders"
        },
        {
            "name": "Obsessive-Compulsive Disorder",
            "code": "300.3",
            "icd11_code": "6B20", 
            "category": "Obsessive-Compulsive and Related Disorders"
        }
    ]
    
    return {
        "status": "success",
        "total_disorders": len(disorders),
        "disorders": disorders
    }

@app.get("/api/v1/search/diagnostic")
async def search_diagnostic_criteria(query: str, disorder: str = None):
    """Search for diagnostic criteria using ChromaDB"""
    try:
        from app.services.knowledge_base_chroma import initialize_chroma_clinical_knowledge
        
        knowledge_base = initialize_chroma_clinical_knowledge()
        results = knowledge_base.search_diagnostic_criteria(query, disorder)
        
        return {
            "status": "success",
            "query": query,
            "disorder": disorder,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        return {"status": "error", "message": f"Search error: {str(e)}"}

@app.get("/api/v1/search/treatment")
async def search_treatment_options(diagnosis: str):
    """Search for treatment options using ChromaDB"""
    try:
        from app.services.knowledge_base_chroma import initialize_chroma_clinical_knowledge
        
        knowledge_base = initialize_chroma_clinical_knowledge()
        results = knowledge_base.search_treatment_options(diagnosis)
        
        return {
            "status": "success",
            "diagnosis": diagnosis,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        return {"status": "error", "message": f"Search error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)