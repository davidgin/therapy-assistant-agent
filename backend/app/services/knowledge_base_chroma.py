"""
Clinical Knowledge Base Service using ChromaDB
Lightweight alternative to FAISS for RAG implementation
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from .vector_database_chroma import ChromaVectorDatabaseService

logger = logging.getLogger(__name__)

class ChromaClinicalKnowledgeBase:
    def __init__(self, chroma_db: ChromaVectorDatabaseService):
        """
        Initialize clinical knowledge base with ChromaDB
        
        Args:
            chroma_db: ChromaDB vector database service instance
        """
        self.chroma_db = chroma_db
        self.knowledge_data_path = "data/knowledge_base"
        
        # Create knowledge base directory
        os.makedirs(self.knowledge_data_path, exist_ok=True)
    
    def load_dsm5_criteria(self) -> List[Dict[str, Any]]:
        """Load DSM-5-TR diagnostic criteria"""
        return [
            {
                "text": "Major Depressive Disorder requires 5 or more symptoms during a 2-week period, with at least one being depressed mood or loss of interest. Symptoms include: depressed mood, diminished interest/pleasure, significant weight loss/gain, insomnia/hypersomnia, psychomotor agitation/retardation, fatigue, feelings of worthlessness, diminished concentration, recurrent thoughts of death.",
                "type": "dsm5_criteria",
                "disorder": "Major Depressive Disorder",
                "code": "296.2x",
                "icd11_code": "6A70",
                "category": "Depressive Disorders",
                "source": "DSM-5-TR"
            },
            {
                "text": "Generalized Anxiety Disorder involves excessive anxiety and worry about multiple events for at least 6 months. The worry is difficult to control and includes symptoms like restlessness, fatigue, concentration difficulties, irritability, muscle tension, and sleep disturbance.",
                "type": "dsm5_criteria", 
                "disorder": "Generalized Anxiety Disorder",
                "code": "300.02",
                "icd11_code": "6B00",
                "category": "Anxiety Disorders",
                "source": "DSM-5-TR"
            },
            {
                "text": "Post-Traumatic Stress Disorder requires exposure to actual/threatened death, serious injury, or sexual violence. Symptoms include intrusive memories, avoidance of trauma-related stimuli, negative cognitions/mood alterations, and arousal/reactivity changes lasting more than 1 month.",
                "type": "dsm5_criteria",
                "disorder": "PTSD", 
                "code": "309.81",
                "icd11_code": "6B40",
                "category": "Trauma and Stressor-Related Disorders",
                "source": "DSM-5-TR"
            },
            {
                "text": "Bipolar I Disorder requires at least one manic episode. Manic episodes involve elevated/irritable mood for at least 1 week with symptoms like grandiosity, decreased sleep need, talkativeness, racing thoughts, distractibility, increased activity, and risky behavior.",
                "type": "dsm5_criteria",
                "disorder": "Bipolar I Disorder",
                "code": "296.4x", 
                "icd11_code": "6A60",
                "category": "Bipolar and Related Disorders",
                "source": "DSM-5-TR"
            },
            {
                "text": "ADHD requires 6+ symptoms of inattention and/or hyperactivity-impulsivity for at least 6 months. Inattention symptoms include difficulty sustaining attention, careless mistakes, not listening, difficulty organizing, avoiding mental effort, losing things, distractibility, forgetfulness.",
                "type": "dsm5_criteria",
                "disorder": "ADHD",
                "code": "314.0x",
                "icd11_code": "6A05", 
                "category": "Neurodevelopmental Disorders",
                "source": "DSM-5-TR"
            },
            {
                "text": "Obsessive-Compulsive Disorder involves obsessions (recurrent intrusive thoughts) and/or compulsions (repetitive behaviors/mental acts). The obsessions/compulsions are time-consuming, cause distress, or significantly impair functioning.",
                "type": "dsm5_criteria",
                "disorder": "OCD",
                "code": "300.3",
                "icd11_code": "6B20",
                "category": "Obsessive-Compulsive and Related Disorders", 
                "source": "DSM-5-TR"
            }
        ]
    
    def load_treatment_guidelines(self) -> List[Dict[str, Any]]:
        """Load evidence-based treatment guidelines"""
        return [
            {
                "text": "Cognitive Behavioral Therapy (CBT) for Major Depression shows strong evidence for effectiveness. CBT focuses on identifying and changing negative thought patterns and behaviors. Treatment typically lasts 16-20 sessions and includes behavioral activation, cognitive restructuring, and relapse prevention.",
                "type": "treatment_guideline",
                "disorder": "Major Depressive Disorder",
                "treatment": "Cognitive Behavioral Therapy",
                "evidence_level": "Level 1 - Strong",
                "duration": "16-20 sessions",
                "source": "APA Clinical Practice Guidelines"
            },
            {
                "text": "SSRI medications are first-line pharmacological treatment for Major Depression. Effective SSRIs include sertraline, fluoxetine, and escitalopram. Treatment response typically occurs within 4-6 weeks, with full benefits at 8-12 weeks.",
                "type": "treatment_guideline",
                "disorder": "Major Depressive Disorder", 
                "treatment": "SSRI Medication",
                "evidence_level": "Level 1 - Strong",
                "source": "APA Clinical Practice Guidelines"
            },
            {
                "text": "CBT for Generalized Anxiety Disorder involves worry exposure, relaxation training, and cognitive restructuring. Treatment focuses on challenging catastrophic thinking, developing coping strategies, and gradual exposure to worry triggers. Duration is typically 12-16 sessions.",
                "type": "treatment_guideline",
                "disorder": "Generalized Anxiety Disorder",
                "treatment": "Cognitive Behavioral Therapy", 
                "evidence_level": "Level 1 - Strong",
                "duration": "12-16 sessions",
                "source": "APA Clinical Practice Guidelines"
            },
            {
                "text": "Trauma-Focused CBT and EMDR are gold-standard treatments for PTSD. TF-CBT includes exposure therapy, cognitive processing, and trauma narrative work. EMDR involves bilateral stimulation while processing traumatic memories.",
                "type": "treatment_guideline",
                "disorder": "PTSD",
                "treatment": "Trauma-Focused CBT and EMDR",
                "evidence_level": "Level 1 - Strong", 
                "source": "APA Clinical Practice Guidelines"
            }
        ]
    
    def initialize_knowledge_base(self) -> None:
        """Initialize the ChromaDB with clinical knowledge"""
        logger.info("Initializing ChromaDB clinical knowledge base...")
        
        # Check if already initialized
        stats = self.chroma_db.get_stats()
        if stats.get('total_documents', 0) > 0:
            logger.info(f"Knowledge base already exists with {stats['total_documents']} documents")
            return
        
        # Load all knowledge base documents
        documents = []
        
        # Add DSM-5-TR criteria
        documents.extend(self.load_dsm5_criteria())
        
        # Add treatment guidelines  
        documents.extend(self.load_treatment_guidelines())
        
        # Add clinical assessments
        documents.extend(self.load_clinical_assessments())
        
        # Add to ChromaDB
        self.chroma_db.add_documents(documents)
        
        logger.info(f"ChromaDB knowledge base initialized with {len(documents)} documents")
    
    def load_clinical_assessments(self) -> List[Dict[str, Any]]:
        """Load clinical assessment tools"""
        return [
            {
                "text": "PHQ-9 (Patient Health Questionnaire-9) is a reliable screening tool for depression severity. Scores: 1-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately severe, 20-27 severe depression. Question 9 assesses suicidal ideation.",
                "type": "assessment_tool",
                "tool_name": "PHQ-9",
                "purpose": "Depression screening and severity",
                "source": "Clinical Assessment"
            },
            {
                "text": "GAD-7 (Generalized Anxiety Disorder-7) screens for anxiety severity. Scores: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-21 severe anxiety. Cut-point of 10 or greater represents reasonable cut-point for identifying GAD.",
                "type": "assessment_tool", 
                "tool_name": "GAD-7",
                "purpose": "Anxiety screening and severity",
                "source": "Clinical Assessment"
            }
        ]
    
    def search_diagnostic_criteria(self, symptoms: str, disorder: str = None) -> List[Dict[str, Any]]:
        """Search for diagnostic criteria based on symptoms"""
        query = f"diagnostic criteria symptoms: {symptoms}"
        
        if disorder:
            results = self.chroma_db.search_by_disorder(query, disorder, k=3)
        else:
            results = self.chroma_db.search(query, k=5)
        
        # Filter for diagnostic criteria
        return [r for r in results if r.get('metadata', {}).get('type') == 'dsm5_criteria']
    
    def search_treatment_options(self, diagnosis: str) -> List[Dict[str, Any]]:
        """Search for treatment options for a specific diagnosis"""
        query = f"treatment therapy intervention for {diagnosis}"
        results = self.chroma_db.search(query, k=5)
        
        # Filter for treatment guidelines
        return [r for r in results if r.get('metadata', {}).get('type') == 'treatment_guideline']
    
    def get_disorder_information(self, disorder: str) -> Dict[str, Any]:
        """Get comprehensive information about a specific disorder"""
        # Search for diagnostic criteria
        criteria_results = self.search_diagnostic_criteria("", disorder)
        
        # Search for treatment options
        treatment_results = self.search_treatment_options(disorder)
        
        return {
            "disorder": disorder,
            "diagnostic_criteria": criteria_results,
            "treatment_options": treatment_results,
            "total_documents": len(criteria_results) + len(treatment_results)
        }

# Initialize knowledge base
def initialize_chroma_clinical_knowledge():
    """Initialize the ChromaDB clinical knowledge base"""
    from .vector_database_chroma import get_chroma_db
    
    chroma_db = get_chroma_db()
    knowledge_base = ChromaClinicalKnowledgeBase(chroma_db)
    
    try:
        knowledge_base.initialize_knowledge_base()
        logger.info("ChromaDB clinical knowledge base initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize ChromaDB knowledge base: {e}")
    
    return knowledge_base