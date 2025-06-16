"""
OpenAI service for RAG (Retrieval-Augmented Generation) in therapy assistant
"""

import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        """Initialize OpenAI service"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"  # Using GPT-4 for clinical accuracy
        
        logger.info("OpenAI service initialized successfully")
    
    def generate_diagnostic_response(
        self, 
        patient_symptoms: str, 
        retrieved_criteria: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate diagnostic suggestions using RAG
        
        Args:
            patient_symptoms: Patient's presenting symptoms
            retrieved_criteria: Relevant diagnostic criteria from ChromaDB
            
        Returns:
            Generated diagnostic response with reasoning
        """
        try:
            # Build context from retrieved documents
            context = self._build_diagnostic_context(retrieved_criteria)
            
            # Create prompt for diagnostic assistance
            prompt = f"""You are an AI assistant helping licensed mental health professionals with diagnostic considerations. 

IMPORTANT DISCLAIMERS:
- You provide educational information only, not medical advice
- Final diagnostic decisions must be made by qualified clinicians
- Always recommend professional clinical judgment and assessment

PATIENT SYMPTOMS:
{patient_symptoms}

RELEVANT DIAGNOSTIC CRITERIA:
{context}

Please provide:
1. Potential diagnostic considerations based on the symptoms and criteria
2. Key diagnostic features that match or don't match
3. Additional assessments that might be helpful
4. Important differential diagnoses to consider
5. Risk factors and protective factors to evaluate

Format your response as a helpful clinical reference, emphasizing the need for comprehensive assessment."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a clinical AI assistant providing educational support to licensed mental health professionals. Always emphasize clinical judgment and comprehensive assessment."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for clinical accuracy
                max_tokens=1000
            )
            
            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "model_used": self.model,
                "retrieved_sources": len(retrieved_criteria),
                "context_used": context[:200] + "..." if len(context) > 200 else context
            }
            
        except Exception as e:
            logger.error(f"Error generating diagnostic response: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate response: {str(e)}"
            }
    
    def generate_treatment_response(
        self, 
        diagnosis: str, 
        patient_context: str,
        retrieved_treatments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate treatment recommendations using RAG
        
        Args:
            diagnosis: Primary diagnosis
            patient_context: Patient background and context
            retrieved_treatments: Relevant treatment guidelines from ChromaDB
            
        Returns:
            Generated treatment recommendations
        """
        try:
            # Build context from retrieved documents
            context = self._build_treatment_context(retrieved_treatments)
            
            prompt = f"""You are an AI assistant helping licensed mental health professionals with evidence-based treatment planning.

IMPORTANT DISCLAIMERS:
- You provide educational information only, not medical advice
- Treatment decisions must be made by qualified clinicians
- Always consider individual patient factors and contraindications

DIAGNOSIS: {diagnosis}

PATIENT CONTEXT:
{patient_context}

EVIDENCE-BASED TREATMENT GUIDELINES:
{context}

Please provide:
1. Evidence-based treatment recommendations
2. Psychotherapy modalities to consider
3. Medication considerations (if applicable)
4. Treatment sequencing and timeline
5. Monitoring and assessment strategies
6. Potential barriers and how to address them

Format as a clinical reference emphasizing individualized care and evidence-based practice."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a clinical AI assistant providing evidence-based treatment guidance to licensed mental health professionals. Emphasize individualized care and clinical judgment."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "model_used": self.model,
                "retrieved_sources": len(retrieved_treatments),
                "context_used": context[:200] + "..." if len(context) > 200 else context
            }
            
        except Exception as e:
            logger.error(f"Error generating treatment response: {e}")
            return {
                "status": "error", 
                "message": f"Failed to generate response: {str(e)}"
            }
    
    def generate_case_analysis(
        self,
        clinical_case: Dict[str, Any],
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive case analysis using RAG
        
        Args:
            clinical_case: Complete clinical case data
            retrieved_knowledge: Relevant knowledge from ChromaDB
            
        Returns:
            Comprehensive case analysis
        """
        try:
            context = self._build_general_context(retrieved_knowledge)
            
            case_summary = f"""
            Demographics: {clinical_case.get('patient_demographics', {})}
            Symptoms: {clinical_case.get('presenting_symptoms', [])}
            History: {clinical_case.get('clinical_history', '')}
            """
            
            prompt = f"""You are an AI assistant providing educational case analysis for mental health professionals.

CLINICAL CASE:
{case_summary}

RELEVANT CLINICAL KNOWLEDGE:
{context}

Provide a comprehensive educational analysis including:
1. Diagnostic formulation with DSM-5-TR considerations
2. Differential diagnosis discussion
3. Risk assessment considerations
4. Treatment planning recommendations
5. Prognosis and outcome factors
6. Cultural and ethical considerations

Emphasize the importance of clinical judgment and comprehensive assessment."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a clinical education AI providing case analysis for mental health professionals. Focus on evidence-based practice and clinical reasoning."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "model_used": self.model,
                "case_id": clinical_case.get('case_id', 'unknown'),
                "retrieved_sources": len(retrieved_knowledge)
            }
            
        except Exception as e:
            logger.error(f"Error generating case analysis: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate analysis: {str(e)}"
            }
    
    def _build_diagnostic_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved diagnostic documents"""
        context_parts = []
        for doc in retrieved_docs:
            metadata = doc.get('metadata', {})
            disorder = metadata.get('disorder', 'Unknown')
            code = metadata.get('code', 'N/A')
            text = doc.get('text', '')
            
            context_parts.append(f"[{disorder} - {code}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _build_treatment_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved treatment documents"""
        context_parts = []
        for doc in retrieved_docs:
            metadata = doc.get('metadata', {})
            treatment = metadata.get('treatment', 'General')
            disorder = metadata.get('disorder', 'Various')
            text = doc.get('text', '')
            
            context_parts.append(f"[{treatment} for {disorder}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _build_general_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Build general context string from retrieved documents"""
        context_parts = []
        for doc in retrieved_docs:
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            doc_type = metadata.get('type', 'knowledge')
            
            context_parts.append(f"[{doc_type}]\n{text}\n")
        
        return "\n".join(context_parts)

# Global service instance
openai_service = None

def get_openai_service() -> OpenAIService:
    """Get the global OpenAI service instance"""
    global openai_service
    if openai_service is None:
        openai_service = OpenAIService()
    return openai_service