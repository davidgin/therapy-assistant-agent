# Pytest configuration and fixtures for therapy-assistant-agent tests

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import tempfile
import os
from typing import AsyncGenerator, Generator

# Import the application components
from app.main_auth_async import app as auth_app
from app.main_web import app as web_app
from app.main_auth_async import (
    Base, 
    User, 
    UserRole, 
    LicenseType, 
    get_async_db,
    hash_password,
    create_access_token
)
from app.services.audio_analysis import AudioAnalysisService


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=None,
        pool_pre_ping=True
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def async_session_factory(async_engine):
    """Create test database session factory."""
    async_session = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    yield async_session


@pytest.fixture(scope="function")
async def async_db(async_engine, async_session_factory):
    """Create test database session."""
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_factory() as session:
        yield session
        await session.rollback()
    
    # Drop tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def sync_db():
    """Create synchronous test database session."""
    engine = create_engine(TEST_SYNC_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def override_get_async_db(async_db):
    """Override the get_async_db dependency for testing."""
    async def _override_get_async_db():
        yield async_db
    
    return _override_get_async_db


@pytest.fixture(scope="function")
def auth_client(override_get_async_db):
    """Create test client for auth app."""
    auth_app.dependency_overrides[get_async_db] = override_get_async_db
    
    with TestClient(auth_app) as client:
        yield client
    
    auth_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def web_client(override_get_async_db):
    """Create test client for web app."""
    web_app.dependency_overrides[get_async_db] = override_get_async_db
    
    with TestClient(web_app) as client:
        yield client
    
    web_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(async_db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpass123"),
        first_name="Test",
        last_name="User",
        role=UserRole.THERAPIST,
        license_type=LicenseType.LMFT,
        license_number="TEST123456",
        license_state="CA",
        is_active=True,
        is_verified=True
    )
    
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    
    yield user


@pytest.fixture(scope="function")
async def test_admin_user(async_db):
    """Create a test admin user."""
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=hash_password("adminpass123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    
    yield user


@pytest.fixture(scope="function")
async def test_student_user(async_db):
    """Create a test student user."""
    user = User(
        email="student@example.com",
        username="studentuser",
        hashed_password=hash_password("studentpass123"),
        first_name="Student",
        last_name="User",
        role=UserRole.STUDENT,
        license_type=LicenseType.STUDENT,
        is_active=True,
        is_verified=True
    )
    
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    
    yield user


@pytest.fixture(scope="function")
def test_token(test_user):
    """Create a test JWT token."""
    token = create_access_token(data={"sub": test_user.email})
    return token


@pytest.fixture(scope="function")
def admin_token(test_admin_user):
    """Create a test admin JWT token."""
    token = create_access_token(data={"sub": test_admin_user.email})
    return token


@pytest.fixture(scope="function")
def student_token(test_student_user):
    """Create a test student JWT token."""
    token = create_access_token(data={"sub": test_student_user.email})
    return token


@pytest.fixture(scope="function")
def auth_headers(test_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    """Create admin authorization headers for testing."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def student_headers(student_token):
    """Create student authorization headers for testing."""
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture(scope="function")
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('app.services.audio_analysis.openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock chat completions
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "positive"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        
        mock_client.chat.completions.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture(scope="function")
def mock_speech_recognizer():
    """Mock speech recognition for testing."""
    with patch('app.services.audio_analysis.sr.Recognizer') as mock_recognizer:
        mock_instance = Mock()
        mock_recognizer.return_value = mock_instance
        
        mock_instance.recognize_google.return_value = "This is test audio transcription"
        mock_instance.record.return_value = Mock()
        
        yield mock_instance


@pytest.fixture(scope="function")
def mock_librosa():
    """Mock librosa for audio analysis testing."""
    with patch('app.services.audio_analysis.librosa') as mock_lib:
        # Mock librosa functions
        mock_lib.load.return_value = ([0.1, 0.2, 0.3], 22050)
        mock_lib.piptrack.return_value = ([[100, 200, 300]], [[0.5, 0.8, 0.6]])
        mock_lib.feature.rms.return_value = [[0.1, 0.2, 0.15]]
        mock_lib.feature.spectral_centroid.return_value = [[1000, 1500, 1200]]
        mock_lib.feature.zero_crossing_rate.return_value = [[0.01, 0.02, 0.015]]
        mock_lib.beat.beat_track.return_value = (120, [1, 2, 3])
        
        yield mock_lib


@pytest.fixture(scope="function")
def sample_audio_data():
    """Sample base64 encoded audio data for testing."""
    # This is a minimal WAV file header + some sample data
    import base64
    
    # Create a simple WAV file in memory
    sample_data = b'\x52\x49\x46\x46\x24\x00\x00\x00\x57\x41\x56\x45\x66\x6D\x74\x20\x10\x00\x00\x00\x01\x00\x01\x00\x40\x1F\x00\x00\x40\x1F\x00\x00\x01\x00\x08\x00\x64\x61\x74\x61\x00\x00\x00\x00'
    
    return base64.b64encode(sample_data).decode('utf-8')


@pytest.fixture(scope="function")
def sample_diagnostic_data():
    """Sample diagnostic data for testing."""
    return {
        "symptoms": "Patient reports feeling sad and anxious for the past two weeks",
        "patient_context": "29-year-old teacher, no previous mental health history"
    }


@pytest.fixture(scope="function")
def sample_treatment_data():
    """Sample treatment data for testing."""
    return {
        "diagnosis": "Major Depressive Disorder",
        "patient_context": "Patient responds well to CBT approaches"
    }


@pytest.fixture(scope="function")
def sample_voice_analysis_data():
    """Sample voice analysis data for testing."""
    return {
        "transcription": "I have been feeling really down lately",
        "sentiment": "negative",
        "emotion": "sad",
        "tone": "depressed",
        "speech_rate": 120.5,
        "pause_frequency": 8.2,
        "confidence": 0.85
    }


@pytest.fixture(scope="function")
def audio_analysis_service():
    """Create AudioAnalysisService instance for testing."""
    return AudioAnalysisService()


@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        yield f.name
    
    # Clean up
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture(scope="function")
def mock_settings():
    """Mock settings for testing."""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-openai-key"
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.DATABASE_URL = TEST_DATABASE_URL
        
        yield mock_settings


@pytest.fixture(scope="function")
def mock_async_openai_client():
    """Mock AsyncOpenAI client for testing."""
    with patch('app.main_auth_async.AsyncOpenAI') as mock_async_openai:
        mock_client = Mock()
        mock_async_openai.return_value = mock_client
        
        # Mock async chat completions
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test AI response for diagnostic analysis"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 100
        
        async def mock_create(*args, **kwargs):
            return mock_response
        
        mock_client.chat.completions.create = mock_create
        
        yield mock_client


# Pytest markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.auth = pytest.mark.auth
pytest.mark.voice = pytest.mark.voice
pytest.mark.web = pytest.mark.web