"""
RAG (Retrieval-Augmented Generation) API endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
import logging

from app.services.vector_database_simple import get_simple_chroma_db
from app.services.openai_service import get_openai_service
from app.utils.data_loader import DataLoader
from app.core.auth import get_current_active_user, require_licensed_professional
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])

@router.get("/diagnose")
async def rag_diagnose(
    symptoms: str = Query(..., description="Patient symptoms description"),
    patient_context: Optional[str] = Query(None, description="Additional patient context"),
    current_user: User = Depends(require_licensed_professional)
):
    """
    AI-powered diagnostic assistance using RAG
    Requires licensed professional access
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
            "user_id": current_user.id,
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

@router.get("/treatment")
async def rag_treatment(
    diagnosis: str = Query(..., description="Primary diagnosis"),
    patient_context: Optional[str] = Query(None, description="Patient background"),
    current_user: User = Depends(require_licensed_professional)
):
    """
    AI-powered treatment recommendations using RAG
    Requires licensed professional access
    """
    try:
        chroma_db = get_simple_chroma_db()
        treatment_query = f"treatment therapy for {diagnosis}"
        retrieved_docs = chroma_db.search(treatment_query, k=5)
        
        treatment_docs = [
            doc for doc in retrieved_docs 
            if doc.get('metadata', {}).get('type') == 'treatment_guideline'
        ]
        
        if not treatment_docs:
            treatment_docs = retrieved_docs[:3]
        
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
            "user_id": current_user.id,
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

@router.get("/case-analysis/{case_id}")
async def rag_case_analysis(
    case_id: str,
    current_user: User = Depends(require_licensed_professional)
):
    """
    Comprehensive case analysis using RAG
    Requires licensed professional access
    """
    try:
        # Load the specific case
        case = DataLoader.get_case_by_id(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Retrieve relevant knowledge for the case
        chroma_db = get_simple_chroma_db()
        
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
            "user_id": current_user.id,
            "knowledge_sources": [
                {
                    "type": doc.get('metadata', {}).get('type'),
                    "disorder": doc.get('metadata', {}).get('disorder'),
                    "score": doc.get('score')
                }
                for doc in retrieved_docs[:5]
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG case analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Case analysis error: {str(e)}")

@router.get("/search/knowledge")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    disorder: Optional[str] = Query(None, description="Filter by disorder"),
    current_user: User = Depends(get_current_active_user)
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
            "user_id": current_user.id,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/knowledge/disorders")
async def get_disorders_list(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of disorders covered in the knowledge base"""
    try:
        chroma_db = get_simple_chroma_db()
        stats = chroma_db.get_stats()
        
        disorders_list = stats.get('disorder_list', [])
        
        return {
            "status": "success",
            "total_disorders": len(disorders_list),
            "disorders": disorders_list,
            "total_documents": stats.get('total_documents', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting disorders list: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/knowledge/types")
async def get_document_types(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of document types in the knowledge base"""
    try:
        chroma_db = get_simple_chroma_db()
        stats = chroma_db.get_stats()
        
        document_types = stats.get('document_types', {})
        
        return {
            "status": "success",
            "document_types": document_types,
            "total_documents": stats.get('total_documents', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting document types: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")