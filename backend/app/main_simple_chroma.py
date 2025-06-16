"""
Simple FastAPI application with ChromaDB (no sentence-transformers dependency)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import create_tables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Therapy Assistant Agent API with Simple ChromaDB...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    # Initialize Simple ChromaDB clinical knowledge base
    try:
        from app.services.vector_database_simple import get_simple_chroma_db
        chroma_db = get_simple_chroma_db()
        
        # Add some sample documents if empty
        stats = chroma_db.get_stats()
        if stats.get('total_documents', 0) == 0:
            logger.info("Initializing ChromaDB with sample clinical data...")
            
            sample_docs = [
                {
                    "text": "Major Depressive Disorder requires 5 or more symptoms during a 2-week period including depressed mood or loss of interest. Symptoms include fatigue, sleep disturbance, concentration problems, and feelings of worthlessness.",
                    "type": "dsm5_criteria",
                    "disorder": "Major Depressive Disorder",
                    "code": "296.2x",
                    "icd11_code": "6A70"
                },
                {
                    "text": "Cognitive Behavioral Therapy (CBT) for depression shows strong evidence for effectiveness. Treatment typically lasts 16-20 sessions and includes behavioral activation and cognitive restructuring.",
                    "type": "treatment_guideline", 
                    "disorder": "Major Depressive Disorder",
                    "treatment": "Cognitive Behavioral Therapy"
                },
                {
                    "text": "Generalized Anxiety Disorder involves excessive anxiety and worry for at least 6 months. Symptoms include restlessness, fatigue, concentration difficulties, irritability, muscle tension, and sleep disturbance.",
                    "type": "dsm5_criteria",
                    "disorder": "Generalized Anxiety Disorder", 
                    "code": "300.02",
                    "icd11_code": "6B00"
                }
            ]
            
            chroma_db.add_documents(sample_docs)
            logger.info("ChromaDB initialized with sample data")
        else:
            logger.info(f"ChromaDB already contains {stats['total_documents']} documents")
            
    except Exception as e:
        logger.warning(f"Could not initialize ChromaDB: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Therapy Assistant Agent API...")

app = FastAPI(
    title="Therapy Assistant Agent API",
    description="AI-powered diagnostic and treatment support with Simple ChromaDB",
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
    return {"message": "Therapy Assistant Agent API with Simple ChromaDB", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running with Simple ChromaDB"}

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
    """Check Simple ChromaDB status"""
    try:
        from app.services.vector_database_simple import get_simple_chroma_db
        chroma_db = get_simple_chroma_db()
        stats = chroma_db.get_stats()
        return {"status": "healthy", "stats": stats}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Simple ChromaDB error: {str(e)}"}

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
    """Search for diagnostic criteria using Simple ChromaDB"""
    try:
        from app.services.vector_database_simple import get_simple_chroma_db
        
        chroma_db = get_simple_chroma_db()
        
        if disorder:
            results = chroma_db.search_by_disorder(query, disorder, k=3)
        else:
            results = chroma_db.search(query, k=5)
        
        # Filter for diagnostic criteria
        criteria_results = [r for r in results if r.get('metadata', {}).get('type') == 'dsm5_criteria']
        
        return {
            "status": "success",
            "query": query,
            "disorder": disorder,
            "results": criteria_results,
            "total_results": len(criteria_results)
        }
    except Exception as e:
        return {"status": "error", "message": f"Search error: {str(e)}"}

@app.get("/api/v1/search/treatment")
async def search_treatment_options(diagnosis: str):
    """Search for treatment options using Simple ChromaDB"""
    try:
        from app.services.vector_database_simple import get_simple_chroma_db
        
        chroma_db = get_simple_chroma_db()
        results = chroma_db.search(f"treatment therapy for {diagnosis}", k=5)
        
        # Filter for treatment guidelines
        treatment_results = [r for r in results if r.get('metadata', {}).get('type') == 'treatment_guideline']
        
        return {
            "status": "success", 
            "diagnosis": diagnosis,
            "results": treatment_results,
            "total_results": len(treatment_results)
        }
    except Exception as e:
        return {"status": "error", "message": f"Search error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)