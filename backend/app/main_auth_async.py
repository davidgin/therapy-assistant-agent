"""
FastAPI application with async authentication and I/O operations
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import timedelta
from typing import Optional
import openai
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import jwt
import secrets
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import aiofiles

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Async OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Convert PostgreSQL URL to async version
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Keep sync engine for Alembic migrations
sync_database_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")
sync_engine = create_engine(sync_database_url, connect_args={"check_same_thread": False} if "sqlite" in sync_database_url else {})

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, select
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    THERAPIST = "therapist"
    PSYCHIATRIST = "psychiatrist"
    PSYCHOLOGIST = "psychologist"
    STUDENT = "student"
    ADMIN = "admin"

class LicenseType(enum.Enum):
    LMFT = "lmft"
    LCSW = "lcsw"
    LPC = "lpc"
    PSYD = "psyd"
    MD = "md"
    PHD = "phd"
    STUDENT = "student"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(Enum(UserRole))
    license_type = Column(Enum(LicenseType), nullable=True)
    license_number = Column(String, nullable=True)
    license_state = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)

# Async database dependency
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Install bcrypt for secure password hashing
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    # Fallback for demo (install passlib for production)
    import hashlib
    pwd_context = None

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    if pwd_context:
        return pwd_context.hash(password)
    else:
        # Fallback - NOT secure for production
        return hashlib.sha256(f"salt_{password}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    if pwd_context:
        return pwd_context.verify(plain_password, hashed_password)
    else:
        # Fallback - NOT secure for production
        return hashlib.sha256(f"salt_{plain_password}".encode()).hexdigest() == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Therapy Assistant Agent API with Async Auth...")
    
    # Create database tables (using sync engine for initial setup)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create demo users
    async with AsyncSessionLocal() as db:
        try:
            # Check if users exist
            result = await db.execute(select(User).where(User.email == "demo.therapist@example.com"))
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create demo users
                demo_users = [
                    User(
                        email="demo.therapist@example.com",
                        username="demo.therapist",
                        hashed_password=hash_password("DemoTherapist123!"),
                        first_name="Demo",
                        last_name="Therapist",
                        role=UserRole.THERAPIST,
                        license_type=LicenseType.LMFT,
                        license_number="LMFT123456",
                        license_state="CA",
                        is_active=True,
                        is_verified=True
                    ),
                    User(
                        email="demo.psychiatrist@example.com",
                        username="demo.psychiatrist",
                        hashed_password=hash_password("DemoDoctor456$"),
                        first_name="Demo",
                        last_name="Psychiatrist",
                        role=UserRole.PSYCHIATRIST,
                        license_type=LicenseType.MD,
                        license_number="MD789012",
                        license_state="CA",
                        is_active=True,
                        is_verified=True
                    ),
                    User(
                        email="demo.student@example.com",
                        username="demo.student",
                        hashed_password=hash_password("StudentDemo789#"),
                        first_name="Demo",
                        last_name="Student",
                        role=UserRole.STUDENT,
                        license_type=LicenseType.STUDENT,
                        is_active=True,
                        is_verified=True
                    ),
                    User(
                        email="admin@therapyassistant.ai",
                        username="admin",
                        hashed_password=hash_password("AdminSecure2024!@"),
                        first_name="Admin",
                        last_name="User",
                        role=UserRole.ADMIN,
                        is_active=True,
                        is_verified=True
                    )
                ]
                
                for user in demo_users:
                    db.add(user)
                await db.commit()
                logger.info("Demo users created")
        except Exception as e:
            logger.error(f"Error creating demo users: {e}")
            await db.rollback()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Therapy Assistant Agent API...")
    await async_engine.dispose()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Therapy Assistant Agent API (Async)",
    description="AI-powered diagnostic and treatment support for mental health professionals",
    version="0.2.0",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],  # Frontend URL from environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Therapy Assistant Agent API (Async Auth Mode)", "version": "0.2.0"}

@app.get("/health")
async def health_check():
    health_status = {"status": "healthy", "message": "API is running with async authentication"}
    
    # Check database connectivity
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(select(1))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check OpenAI connectivity
    if openai_client:
        health_status["openai"] = "configured"
    else:
        health_status["openai"] = "not configured"
    
    return health_status

from pydantic import BaseModel, validator
import re
from .services.audio_analysis import audio_analysis_service

def validate_password_strength(password: str) -> str:
    """Validate password meets security requirements"""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must be less than 128 characters long")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")
    return password

class LoginRequest(BaseModel):
    username: str
    password: str

class RegistrationRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    
    @validator('password')
    def validate_password(cls, v):
        return validate_password_strength(v)

class DiagnosticRequest(BaseModel):
    symptoms: str
    patient_context: Optional[str] = None

class TreatmentRequest(BaseModel):
    diagnosis: str
    patient_context: Optional[str] = None

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    """Async login endpoint"""
    result = await db.execute(select(User).where(User.email == login_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "license_type": user.license_type.value if user.license_type else None,
            "license_number": user.license_number,
            "license_state": user.license_state,
            "organization": user.organization,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }

@app.post("/api/auth/register")
@limiter.limit("3/minute")
async def register(request: Request, registration_data: RegistrationRequest, db: AsyncSession = Depends(get_async_db)):
    """Async register a new user"""
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.email == registration_data.email) | 
            (User.username == registration_data.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = hash_password(registration_data.password)
    new_user = User(
        email=registration_data.email,
        username=registration_data.username,
        hashed_password=hashed_password,
        first_name=registration_data.first_name,
        last_name=registration_data.last_name,
        role=UserRole.STUDENT,  # Default role for new registrations
        license_type=LicenseType.STUDENT,
        is_active=True,
        is_verified=False  # Require email verification
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "role": new_user.role.value
        }
    }

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.get("/api/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_async_db)):
    """Get current user info - async"""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "license_type": user.license_type.value if user.license_type else None,
        "license_number": user.license_number,
        "license_state": user.license_state,
        "organization": user.organization,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

@app.get("/api/v1/synthetic-cases")
async def get_synthetic_cases():
    """Get synthetic clinical cases - async file reading"""
    try:
        # Use aiofiles for async file reading
        cases_file = "backend/data/synthetic/synthetic_clinical_cases.json"
        try:
            async with aiofiles.open(cases_file, 'r') as f:
                import json
                content = await f.read()
                cases_data = json.loads(content)
                cases = cases_data.get("cases", [])
        except FileNotFoundError:
            # Fallback to mock data
            cases = [
                {
                    "case_id": "CASE_001",
                    "patient_demographics": {
                        "age": 28,
                        "gender": "Female",
                        "occupation": "Teacher"
                    },
                    "presenting_symptoms": ["Persistent sadness", "Loss of interest", "Fatigue"],
                    "clinical_history": "Patient reports 3 months of low mood...",
                    "suggested_diagnosis": {
                        "primary": "Major Depressive Disorder",
                        "dsm5_code": "296.22",
                        "confidence": 0.85
                    },
                    "severity": "moderate"
                }
            ]
        
        return {
            "status": "success",
            "total_cases": len(cases),
            "cases": cases
        }
    except Exception as e:
        logger.error(f"Error loading synthetic cases: {e}")
        return {"status": "error", "message": "Failed to load cases"}

@app.get("/api/v1/rag/diagnose")
@limiter.limit("10/minute")
async def get_diagnostic_assistance(request: Request, symptoms: str, patient_context: str = ""):
    """Get AI-powered diagnostic assistance - async OpenAI calls"""
    if not openai_client:
        return {"status": "error", "message": "OpenAI service not available"}
    
    try:
        # Create a clinical prompt for diagnostic assistance
        prompt = f"""You are an expert clinical psychologist providing diagnostic assistance based on DSM-5-TR criteria. 

Patient Symptoms: {symptoms}

Patient Context: {patient_context}

Please provide a professional clinical analysis including:
1. **Primary Differential Diagnoses** (list 2-3 most likely diagnoses with DSM-5-TR codes)
2. **Clinical Reasoning** (explain why these diagnoses are being considered)
3. **Additional Assessment Recommendations** (what further evaluation is needed)
4. **Risk Factors** (any immediate concerns or risk factors to consider)

Important: This is for educational and clinical support purposes only. All final diagnostic decisions must be made by qualified mental health professionals through comprehensive clinical assessment.

Provide a structured, evidence-based response."""

        # Async OpenAI API call
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a clinical psychology expert providing diagnostic assistance based on DSM-5-TR criteria. Always emphasize that final diagnosis requires comprehensive clinical assessment by qualified professionals."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "status": "success",
            "ai_response": {
                "response": ai_response,
                "model_used": "gpt-4",
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0
            },
            "query": {
                "symptoms": symptoms,
                "patient_context": patient_context
            }
        }
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {
            "status": "error",
            "message": f"AI service error: {str(e)}"
        }

@app.get("/api/v1/rag/treatment")
@limiter.limit("10/minute")
async def get_treatment_recommendations(request: Request, diagnosis: str, patient_context: str = ""):
    """Get AI-powered treatment recommendations - async"""
    if not openai_client:
        return {"status": "error", "message": "OpenAI service not available"}
    
    try:
        prompt = f"""You are an expert clinical psychologist providing evidence-based treatment recommendations.

Diagnosis: {diagnosis}

Patient Context: {patient_context}

Please provide comprehensive treatment recommendations including:
1. **Primary Treatment Approaches** (evidence-based therapies most effective for this diagnosis)
2. **Treatment Goals** (specific, measurable therapeutic objectives)
3. **Intervention Strategies** (specific techniques and approaches)
4. **Timeline and Frequency** (recommended session frequency and duration)
5. **Potential Challenges** (common obstacles and how to address them)
6. **Outcome Measures** (how to track progress)

Important: All treatment must be provided by qualified mental health professionals. This is for educational and clinical support purposes only.

Provide structured, evidence-based recommendations following best practices."""

        # Async OpenAI API call
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a clinical psychology expert providing evidence-based treatment recommendations. Always emphasize professional supervision and evidence-based practices."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "status": "success",
            "ai_response": {
                "response": ai_response,
                "model_used": "gpt-4",
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0
            },
            "query": {
                "diagnosis": diagnosis,
                "patient_context": patient_context
            }
        }
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {
            "status": "error",
            "message": f"AI service error: {str(e)}"
        }

@app.get("/api/v1/case-analysis/{case_id}")
@limiter.limit("5/minute")
async def get_case_analysis(request: Request, case_id: str):
    """Get comprehensive case analysis - async"""
    if not openai_client:
        return {"status": "error", "message": "OpenAI service not available"}
    
    try:
        # Load case data asynchronously
        cases_file = "backend/data/synthetic/synthetic_clinical_cases.json"
        case_data = None
        
        try:
            async with aiofiles.open(cases_file, 'r') as f:
                import json
                content = await f.read()
                cases_json = json.loads(content)
                cases = cases_json.get("cases", [])
                case_data = next((case for case in cases if case["case_id"] == case_id), None)
        except FileNotFoundError:
            pass
        
        if not case_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Create comprehensive analysis prompt
        prompt = f"""Analyze this clinical case comprehensively:

Case ID: {case_data['case_id']}
Patient Demographics: {case_data.get('patient_demographics', {})}
Presenting Symptoms: {', '.join(case_data.get('presenting_symptoms', []))}
Clinical History: {case_data.get('clinical_history', '')}
Current Diagnosis: {case_data.get('suggested_diagnosis', {}).get('primary', '')}

Provide a comprehensive clinical analysis including:
1. **Diagnostic Accuracy Assessment** (evaluate the suggested diagnosis)
2. **Differential Diagnosis Considerations** (alternative diagnoses to consider)
3. **Risk Assessment** (immediate and long-term risk factors)
4. **Treatment Recommendations** (evidence-based interventions)
5. **Prognosis** (likely outcomes with appropriate treatment)
6. **Clinical Insights** (key observations and professional considerations)

This is for educational and clinical training purposes."""

        # Async OpenAI API call
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert clinical supervisor providing comprehensive case analysis for educational purposes. Focus on evidence-based assessment and treatment planning."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "status": "success",
            "case_id": case_id,
            "case_data": case_data,
            "ai_analysis": {
                "response": ai_response,
                "model_used": "gpt-4",
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0
            },
            "retrieved_documents": 0,  # Placeholder for future RAG integration
            "knowledge_sources": []  # Placeholder for future RAG integration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Case analysis error: {e}")
        return {
            "status": "error",
            "message": f"Analysis error: {str(e)}"
        }

# Voice Analysis Endpoints
class VoiceTranscriptionRequest(BaseModel):
    audio_data: str  # base64 encoded audio

class VoiceAnalysisRequest(BaseModel):
    audio_data: str  # base64 encoded audio

@app.post("/voice/transcribe")
@limiter.limit("10/minute")
async def transcribe_audio(
    request: Request,
    voice_request: VoiceTranscriptionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio to text using speech recognition"""
    try:
        logger.info(f"Transcribing audio for user: {current_user.email}")
        
        # Validate user is licensed
        if not current_user.is_licensed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voice analysis requires licensed practitioner"
            )
        
        # Transcribe audio
        transcription = await audio_analysis_service.transcribe_audio(voice_request.audio_data)
        
        logger.info(f"Audio transcription completed for user: {current_user.email}")
        
        return {"transcription": transcription}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audio transcription failed"
        )

@app.post("/voice/analyze")
@limiter.limit("10/minute")
async def analyze_voice(
    request: Request,
    voice_request: VoiceAnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive voice analysis including transcription, tone, and emotion detection"""
    try:
        logger.info(f"Analyzing voice for user: {current_user.email}")
        
        # Validate user is licensed
        if not current_user.is_licensed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voice analysis requires licensed practitioner"
            )
        
        # Perform comprehensive voice analysis
        analysis = await audio_analysis_service.analyze_voice_comprehensive(voice_request.audio_data)
        
        logger.info(f"Voice analysis completed for user: {current_user.email}")
        
        return {
            "transcription": analysis.transcription,
            "sentiment": analysis.sentiment,
            "emotion": analysis.emotion,
            "tone": analysis.tone,
            "speechRate": analysis.speech_rate,
            "pauseFrequency": analysis.pause_frequency,
            "confidence": analysis.confidence
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice analysis error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice analysis failed"
        )

@app.get("/voice/health")
async def voice_health_check():
    """Health check for voice analysis service"""
    return {
        "status": "healthy",
        "service": "voice_analysis",
        "features": [
            "transcription",
            "tone_analysis",
            "emotion_detection",
            "speech_rate_analysis",
            "pause_frequency_analysis"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)