"""
Configuration settings for the therapy assistant application
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    PROJECT_NAME: str = "Therapy Assistant Agent API"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://therapy_user:therapy_pass@localhost:5432/therapy_assistant"
    DATABASE_ECHO: bool = False  # Set to True for SQL query logging
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 1500
    OPENAI_TEMPERATURE: float = 0.3
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = "chromadb"  # "chromadb" or "faiss"
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH: str = "data/knowledge"
    SYNTHETIC_DATA_PATH: str = "data/synthetic"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://frontend:3000"
    ]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".json", ".csv", ".txt", ".pdf"]
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        if not v or not v.startswith(("postgresql://", "sqlite:///")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL or SQLite URL")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is not default in production"""
        if v == "your-secret-key-change-in-production":
            import warnings
            warnings.warn(
                "Using default SECRET_KEY in production is insecure. "
                "Please set a unique SECRET_KEY environment variable.",
                UserWarning
            )
        return v
    
    @validator("OPENAI_API_KEY", pre=True)
    def validate_openai_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate OpenAI API key format"""
        if v and not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        return v
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: List[str]) -> List[str]:
        """Ensure CORS origins are properly formatted"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"

class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "WARNING"

class TestingSettings(Settings):
    """Testing environment settings"""
    DATABASE_URL: str = "sqlite:///./test.db"
    SECRET_KEY: str = "test-secret-key"
    OPENAI_API_KEY: str = "sk-test-key-for-testing"

def get_settings() -> Settings:
    """Get settings based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Logging configuration
import logging

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log")
        ]
    )
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

# Application metadata
APP_METADATA = {
    "title": settings.PROJECT_NAME,
    "description": "AI-powered diagnostic and treatment support for mental health professionals",
    "version": settings.VERSION,
    "contact": {
        "name": "Therapy Assistant Team",
        "email": "support@therapyassistant.ai"
    },
    "license_info": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    "tags_metadata": [
        {
            "name": "Authentication",
            "description": "User authentication and authorization"
        },
        {
            "name": "RAG",
            "description": "Retrieval-Augmented Generation for clinical assistance"
        },
        {
            "name": "Cases",
            "description": "Clinical case management and analysis"
        },
        {
            "name": "Knowledge",
            "description": "Clinical knowledge base and search"
        }
    ]
}