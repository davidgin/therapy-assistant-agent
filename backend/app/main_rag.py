"""
FastAPI application with full RAG implementation using ChromaDB + OpenAI
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import json
import os
from typing import Optional

from app.core.database import create_tables
from app.services.vector_database_simple import get_simple_chroma_db
from app.services.openai_service import get_openai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Therapy Assistant Agent API with Full RAG...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    # Initialize ChromaDB with comprehensive knowledge base
    try:
        chroma_db = get_simple_chroma_db()
        stats = chroma_db.get_stats()
        
        if stats.get('total_documents', 0) == 0:
            logger.info("Initializing ChromaDB with comprehensive clinical knowledge...")
            
            # Load comprehensive knowledge base
            knowledge_file = "data/knowledge/clinical_knowledge_base.json"
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r') as f:
                    knowledge_docs = json.load(f)
                
                chroma_db.add_documents(knowledge_docs)
                logger.info(f"Added {len(knowledge_docs)} knowledge documents to ChromaDB")
            
            # Add sample diagnostic data if needed
            sample_docs = [
                {
                    "text": "Persistent Depressive Disorder (Dysthymia) involves depressed mood for most days for at least 2 years (1 year in children/adolescents). Symptoms include poor appetite, insomnia, low energy, poor concentration, feelings of hopelessness. Never without symptoms for more than 2 months during the period.",
                    "type": "dsm5_criteria",
                    "disorder": "Persistent Depressive Disorder",
                    "code": "300.4",
                    "icd11_code": "6A71"
                },
                {
                    "text": "Interpersonal Therapy (IPT) for depression focuses on improving interpersonal relationships and social functioning. Treatment addresses grief, role disputes, role transitions, and interpersonal deficits. Typically 12-16 sessions with strong evidence base comparable to CBT.",
                    "type": "treatment_guideline",
                    "disorder": "Major Depressive Disorder",
                    "treatment": "Interpersonal Therapy",
                    "evidence_level": "A"
                }
            ]
            
            chroma_db.add_documents(sample_docs)
            
            final_stats = chroma_db.get_stats()
            logger.info(f"ChromaDB initialized with {final_stats['total_documents']} total documents")
        else:
            logger.info(f"ChromaDB already contains {stats['total_documents']} documents")
            
    except Exception as e:
        logger.warning(f"Could not initialize ChromaDB knowledge base: {e}")
    
    # Test OpenAI service
    try:
        openai_service = get_openai_service()
        logger.info("OpenAI service initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize OpenAI service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Therapy Assistant Agent API...")

app = FastAPI(
    title="Therapy Assistant Agent API with RAG",
    description="AI-powered diagnostic and treatment support using Retrieval-Augmented Generation",
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Therapy Assistant Agent API with Full RAG", "version": "0.2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running with ChromaDB + OpenAI RAG"}

@app.get("/health/services")
async def services_health():
    """Check all service statuses"""
    status = {"services": {}}
    
    # Check ChromaDB
    try:
        chroma_db = get_simple_chroma_db()
        stats = chroma_db.get_stats()
        status["services"]["chromadb"] = {"status": "healthy", "stats": stats}
    except Exception as e:
        status["services"]["chromadb"] = {"status": "unhealthy", "error": str(e)}
    
    # Check OpenAI
    try:
        openai_service = get_openai_service()
        status["services"]["openai"] = {"status": "healthy", "model": "gpt-4"}
    except Exception as e:
        status["services"]["openai"] = {"status": "unhealthy", "error": str(e)}
    
    return status

@app.get("/api/v1/synthetic-cases")
async def get_synthetic_cases():
    """Get synthetic clinical cases for testing"""
    try:
        data_file = "data/synthetic/synthetic_clinical_cases.json"
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                cases = json.load(f)
            
            return {
                "status": "success",
                "total_cases": len(cases),
                "cases": cases
            }
        else:
            return {"status": "error", "message": "Synthetic data file not found"}
            
    except Exception as e:
        return {"status": "error", "message": f"Error loading synthetic cases: {str(e)}"}

@app.get("/api/v1/rag/diagnose")
async def rag_diagnose(
    symptoms: str = Query(..., description="Patient symptoms description"),
    patient_context: Optional[str] = Query(None, description="Additional patient context")
):
    """
    AI-powered diagnostic assistance using RAG
    Retrieves relevant diagnostic criteria and generates response using OpenAI
    """
    try:
        # Retrieve relevant diagnostic criteria
        chroma_db = get_simple_chroma_db()
        retrieved_docs = chroma_db.search(symptoms, k=5)
        
        # Filter for diagnostic criteria
        diagnostic_docs = [
            doc for doc in retrieved_docs 
            if doc.get('metadata', {}).get('type') == 'dsm5_criteria'
        ]
        
        if not diagnostic_docs:
            # Fall back to all retrieved docs if no specific criteria found
            diagnostic_docs = retrieved_docs[:3]
        
        # Generate AI response using RAG
        openai_service = get_openai_service()
        full_context = f"Symptoms: {symptoms}"
        if patient_context:
            full_context += f"\nContext: {patient_context}"
            
        response = openai_service.generate_diagnostic_response(
            patient_symptoms=full_context,
            retrieved_criteria=diagnostic_docs
        )
        
        return {
            "status": "success",
            "query": symptoms,
            "patient_context": patient_context,
            "retrieved_documents": len(diagnostic_docs),
            "ai_response": response,
            "retrieved_sources": [
                {
                    "disorder": doc.get('metadata', {}).get('disorder'),
                    "code": doc.get('metadata', {}).get('code'),
                    "score": doc.get('score')
                }
                for doc in diagnostic_docs
            ]
        }
        
    except Exception as e:
        logger.error(f"RAG diagnosis error: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnosis error: {str(e)}")

@app.get("/api/v1/rag/treatment")
async def rag_treatment(
    diagnosis: str = Query(..., description="Primary diagnosis"),
    patient_context: Optional[str] = Query(None, description="Patient background and context")
):
    """
    AI-powered treatment recommendations using RAG
    Retrieves relevant treatment guidelines and generates response using OpenAI
    """
    try:
        # Retrieve relevant treatment information
        chroma_db = get_simple_chroma_db()
        treatment_query = f"treatment therapy for {diagnosis}"
        retrieved_docs = chroma_db.search(treatment_query, k=5)
        
        # Filter for treatment guidelines
        treatment_docs = [
            doc for doc in retrieved_docs 
            if doc.get('metadata', {}).get('type') == 'treatment_guideline'
        ]
        
        if not treatment_docs:
            # Fall back to all retrieved docs
            treatment_docs = retrieved_docs[:3]
        
        # Generate AI response using RAG
        openai_service = get_openai_service()
        response = openai_service.generate_treatment_response(
            diagnosis=diagnosis,
            patient_context=patient_context or "No additional context provided",
            retrieved_treatments=treatment_docs
        )
        
        return {
            "status": "success",
            "diagnosis": diagnosis,
            "patient_context": patient_context,
            "retrieved_documents": len(treatment_docs),
            "ai_response": response,
            "retrieved_sources": [
                {
                    "treatment": doc.get('metadata', {}).get('treatment'),
                    "disorder": doc.get('metadata', {}).get('disorder'),
                    "evidence_level": doc.get('metadata', {}).get('evidence_level'),
                    "score": doc.get('score')
                }
                for doc in treatment_docs
            ]
        }
        
    except Exception as e:
        logger.error(f"RAG treatment error: {e}")
        raise HTTPException(status_code=500, detail=f"Treatment error: {str(e)}")

@app.get("/api/v1/rag/case-analysis/{case_id}")
async def rag_case_analysis(case_id: str):
    """
    Comprehensive case analysis using RAG
    Analyzes a clinical case using retrieved knowledge and AI generation
    """
    try:
        # Load the specific case
        data_file = "data/synthetic/synthetic_clinical_cases.json"
        if not os.path.exists(data_file):
            raise HTTPException(status_code=404, detail="Clinical cases not found")
        
        with open(data_file, 'r') as f:
            cases = json.load(f)
        
        # Find the requested case
        case = None
        for c in cases:
            if c.get('case_id') == case_id:
                case = c
                break
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Retrieve relevant knowledge for the case
        chroma_db = get_simple_chroma_db()
        
        # Search based on symptoms and suggested diagnosis
        symptoms_text = " ".join(case.get('presenting_symptoms', []))
        diagnosis = case.get('suggested_diagnosis', {}).get('primary', '')
        search_query = f"{symptoms_text} {diagnosis}"
        
        retrieved_docs = chroma_db.search(search_query, k=8)
        
        # Generate comprehensive analysis
        openai_service = get_openai_service()
        response = openai_service.generate_case_analysis(
            clinical_case=case,
            retrieved_knowledge=retrieved_docs
        )
        
        return {
            "status": "success",
            "case_id": case_id,
            "case_data": case,
            "retrieved_documents": len(retrieved_docs),
            "ai_analysis": response,
            "knowledge_sources": [
                {
                    "type": doc.get('metadata', {}).get('type'),
                    "disorder": doc.get('metadata', {}).get('disorder'),
                    "score": doc.get('score')
                }
                for doc in retrieved_docs[:5]  # Top 5 sources
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG case analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Case analysis error: {str(e)}")

@app.get("/api/v1/search/knowledge")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    disorder: Optional[str] = Query(None, description="Filter by disorder")
):
    """Search the clinical knowledge base"""
    try:
        chroma_db = get_simple_chroma_db()
        
        if disorder:
            results = chroma_db.search_by_disorder(query, disorder, k=10)
        else:
            results = chroma_db.search(query, k=10)
        
        # Filter by document type if specified
        if doc_type:
            results = [
                r for r in results 
                if r.get('metadata', {}).get('type') == doc_type
            ]
        
        return {
            "status": "success",
            "query": query,
            "filters": {"doc_type": doc_type, "disorder": disorder},
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)