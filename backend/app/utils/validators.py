"""
Input validation utilities for the therapy assistant application
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, validator, Field
from datetime import datetime

class DiagnosticRequestValidator(BaseModel):
    """Validator for diagnostic assistance requests"""
    symptoms: str = Field(..., min_length=10, max_length=2000)
    patient_context: Optional[str] = Field(None, max_length=1000)
    
    @validator('symptoms')
    def validate_symptoms(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Symptoms cannot be empty")
        
        # Check for potentially harmful content
        forbidden_patterns = [
            r'\b(harm|kill|suicide)\b',
            r'\b(medication.*dosage)\b',
            r'\b(prescription.*change)\b'
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, v.lower()):
                raise ValueError("Input contains content requiring immediate clinical attention")
        
        return v.strip()

class TreatmentRequestValidator(BaseModel):
    """Validator for treatment planning requests"""
    diagnosis: str = Field(..., min_length=3, max_length=200)
    patient_context: Optional[str] = Field(None, max_length=1000)
    
    @validator('diagnosis')
    def validate_diagnosis(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Diagnosis cannot be empty")
        
        # Basic format validation
        if len(v.strip()) < 3:
            raise ValueError("Diagnosis must be at least 3 characters")
        
        return v.strip()

class UserRegistrationValidator(BaseModel):
    """Validator for user registration"""
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for required character types
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not all([has_upper, has_lower, has_digit]):
            raise ValueError("Password must contain uppercase, lowercase, and numeric characters")
        
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if not v.replace(" ", "").replace("-", "").replace("'", "").isalpha():
            raise ValueError("Names can only contain letters, spaces, hyphens, and apostrophes")
        
        return v.strip().title()

class CaseAnalysisValidator(BaseModel):
    """Validator for case analysis requests"""
    case_id: str = Field(..., regex=r'^[A-Z0-9_-]+$', max_length=50)
    
    @validator('case_id')
    def validate_case_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Case ID cannot be empty")
        
        return v.strip().upper()

class KnowledgeSearchValidator(BaseModel):
    """Validator for knowledge base search"""
    query: str = Field(..., min_length=2, max_length=500)
    doc_type: Optional[str] = Field(None, regex=r'^[a-z_]+$')
    disorder: Optional[str] = Field(None, max_length=100)
    
    @validator('query')
    def validate_query(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Search query cannot be empty")
        
        # Remove potentially harmful characters
        cleaned = re.sub(r'[<>{}();]', '', v)
        return cleaned.strip()

def validate_clinical_content(text: str) -> bool:
    """
    Validate that clinical content is appropriate and safe
    
    Args:
        text: Text content to validate
        
    Returns:
        True if content is valid, False otherwise
    """
    if not text or len(text.strip()) == 0:
        return False
    
    # Check for SQL injection patterns
    sql_patterns = [
        r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b',
        r'[\'";].*[\'";]',
        r'--.*$'
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    # Check for script injection
    script_patterns = [
        r'<script.*?>',
        r'javascript:',
        r'on\w+\s*='
    ]
    
    for pattern in script_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    return True

def sanitize_user_input(text: str) -> str:
    """
    Sanitize user input for safe processing
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>{}();]', '', text)
    
    # Limit length
    if len(sanitized) > 2000:
        sanitized = sanitized[:2000] + "..."
    
    # Strip whitespace
    return sanitized.strip()

def validate_file_upload(filename: str, content_type: str, file_size: int) -> Dict[str, Any]:
    """
    Validate file upload parameters
    
    Args:
        filename: Name of uploaded file
        content_type: MIME type of file
        file_size: Size of file in bytes
        
    Returns:
        Validation result with status and messages
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Validate filename
    if not filename or len(filename) == 0:
        result["valid"] = False
        result["errors"].append("Filename cannot be empty")
    
    # Check file extension
    allowed_extensions = ['.json', '.csv', '.txt', '.pdf']
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if f'.{file_ext}' not in allowed_extensions:
        result["valid"] = False
        result["errors"].append(f"File type .{file_ext} not allowed")
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024
    if file_size > max_size:
        result["valid"] = False
        result["errors"].append(f"File size {file_size} exceeds maximum {max_size} bytes")
    
    # Validate content type
    allowed_types = [
        'application/json',
        'text/csv',
        'text/plain',
        'application/pdf'
    ]
    if content_type not in allowed_types:
        result["warnings"].append(f"Unexpected content type: {content_type}")
    
    return result

def validate_datetime_range(start_date: str, end_date: str) -> bool:
    """
    Validate datetime range parameters
    
    Args:
        start_date: Start date string
        end_date: End date string
        
    Returns:
        True if range is valid
    """
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Check if start is before end
        if start >= end:
            return False
        
        # Check if range is reasonable (not more than 1 year)
        if (end - start).days > 365:
            return False
        
        return True
        
    except (ValueError, AttributeError):
        return False

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)