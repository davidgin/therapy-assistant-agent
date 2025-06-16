"""
Data loading utilities for synthetic cases and knowledge base
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DataLoader:
    """Utility class for loading synthetic data and knowledge base"""
    
    @staticmethod
    def load_synthetic_cases(file_path: str = "data/synthetic/synthetic_clinical_cases.json") -> List[Dict[str, Any]]:
        """Load synthetic clinical cases from JSON file"""
        try:
            if not Path(file_path).exists():
                logger.warning(f"Synthetic cases file not found: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            logger.info(f"Loaded {len(cases)} synthetic clinical cases")
            return cases
            
        except Exception as e:
            logger.error(f"Error loading synthetic cases: {e}")
            return []
    
    @staticmethod
    def load_clinical_knowledge(file_path: str = "data/knowledge/clinical_knowledge_base.json") -> List[Dict[str, Any]]:
        """Load clinical knowledge base from JSON file"""
        try:
            if not Path(file_path).exists():
                logger.warning(f"Knowledge base file not found: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
            
            logger.info(f"Loaded {len(knowledge)} knowledge base documents")
            return knowledge
            
        except Exception as e:
            logger.error(f"Error loading clinical knowledge: {e}")
            return []
    
    @staticmethod
    def get_case_by_id(case_id: str, cases: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Get a specific case by ID"""
        if cases is None:
            cases = DataLoader.load_synthetic_cases()
        
        for case in cases:
            if case.get('case_id') == case_id:
                return case
        
        return None
    
    @staticmethod
    def get_knowledge_by_disorder(disorder: str, knowledge: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Get knowledge documents for a specific disorder"""
        if knowledge is None:
            knowledge = DataLoader.load_clinical_knowledge()
        
        filtered_knowledge = []
        for doc in knowledge:
            if doc.get('disorder', '').lower() == disorder.lower():
                filtered_knowledge.append(doc)
        
        return filtered_knowledge
    
    @staticmethod
    def get_knowledge_by_type(doc_type: str, knowledge: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Get knowledge documents by type (dsm5_criteria, treatment_guideline, etc.)"""
        if knowledge is None:
            knowledge = DataLoader.load_clinical_knowledge()
        
        filtered_knowledge = []
        for doc in knowledge:
            if doc.get('type', '').lower() == doc_type.lower():
                filtered_knowledge.append(doc)
        
        return filtered_knowledge
    
    @staticmethod
    def validate_case_data(case: Dict[str, Any]) -> bool:
        """Validate that a case has required fields"""
        required_fields = ['case_id', 'patient_demographics', 'presenting_symptoms']
        
        for field in required_fields:
            if field not in case:
                logger.warning(f"Case missing required field: {field}")
                return False
        
        return True
    
    @staticmethod
    def validate_knowledge_data(knowledge_doc: Dict[str, Any]) -> bool:
        """Validate that a knowledge document has required fields"""
        required_fields = ['text', 'type']
        
        for field in required_fields:
            if field not in knowledge_doc:
                logger.warning(f"Knowledge document missing required field: {field}")
                return False
        
        return True