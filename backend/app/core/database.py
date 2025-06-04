"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://therapy_user:therapy_pass@localhost:5432/therapy_assistant"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db() -> Generator:
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database
    """
    Base.metadata.create_all(bind=engine)