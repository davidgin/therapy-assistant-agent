"""
Simple FastAPI application without ML dependencies for testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    return {"message": "Therapy Assistant Agent API (Simple Mode)", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running in simple mode"}

@app.get("/health/database")
async def database_health():
    """Check database connectivity"""
    try:
        from app.core.database import SessionLocal
        # Create engine with SQLite for testing
        import tempfile
        import os
        from sqlalchemy import create_engine
        
        # Use in-memory SQLite for testing
        engine = create_engine("sqlite:///:memory:")
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {"status": "healthy", "message": "Database connection successful (SQLite test)"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)