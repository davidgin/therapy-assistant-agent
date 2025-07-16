# Unit tests for authentication endpoints

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json

from app.main_auth_async import (
    User,
    UserRole,
    LicenseType,
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    validate_password_strength
)


@pytest.mark.unit
@pytest.mark.auth
class TestAuthenticationEndpoints:
    """Test cases for authentication endpoints."""
    
    def test_root_endpoint(self, auth_client):
        """Test root endpoint."""
        response = auth_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Therapy Assistant Agent API" in data["message"]
    
    def test_health_check(self, auth_client):
        """Test health check endpoint."""
        response = auth_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "openai" in data
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_client, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }
        
        response = auth_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["role"] == test_user.role.value
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_client, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = auth_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "Incorrect email or password" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, auth_client):
        """Test login with nonexistent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = auth_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "Incorrect email or password" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, auth_client, async_db):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password=hash_password("password123"),
            first_name="Inactive",
            last_name="User",
            role=UserRole.THERAPIST,
            is_active=False,
            is_verified=True
        )
        async_db.add(inactive_user)
        await async_db.commit()
        
        login_data = {
            "username": "inactive@example.com",
            "password": "password123"
        }
        
        response = auth_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "Inactive user" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_success(self, auth_client):
        """Test successful user registration."""
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = auth_client.post("/api/auth/register", json=register_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "User registered successfully" in data["message"]
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["role"] == "student"  # Default role
    
    @pytest.mark.asyncio
    async def test_register_existing_email(self, auth_client, test_user):
        """Test registration with existing email."""
        register_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "NewPassword123!",
            "first_name": "Different",
            "last_name": "User"
        }
        
        response = auth_client.post("/api/auth/register", json=register_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_existing_username(self, auth_client, test_user):
        """Test registration with existing username."""
        register_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "NewPassword123!",
            "first_name": "Different",
            "last_name": "User"
        }
        
        response = auth_client.post("/api/auth/register", json=register_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, auth_client):
        """Test registration with weak password."""
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "weak",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = auth_client.post("/api/auth/register", json=register_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, auth_client, test_user, auth_headers):
        """Test getting current user information."""
        response = auth_client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["role"] == test_user.role.value
        assert data["is_active"] == test_user.is_active
    
    def test_get_current_user_no_token(self, auth_client):
        """Test getting current user without token."""
        response = auth_client.get("/api/auth/me")
        assert response.status_code == 403
    
    def test_get_current_user_invalid_token(self, auth_client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = auth_client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_synthetic_cases(self, auth_client):
        """Test getting synthetic cases."""
        response = auth_client.get("/api/v1/synthetic-cases")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        assert "cases" in data
        assert isinstance(data["cases"], list)
    
    @pytest.mark.asyncio
    async def test_diagnostic_assistance_no_openai(self, auth_client):
        """Test diagnostic assistance without OpenAI."""
        with patch('app.main_auth_async.openai_client', None):
            response = auth_client.get("/api/v1/rag/diagnose?symptoms=test+symptoms")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "error"
            assert "OpenAI service not available" in data["message"]
    
    @pytest.mark.asyncio
    async def test_diagnostic_assistance_with_openai(self, auth_client, mock_async_openai_client):
        """Test diagnostic assistance with OpenAI."""
        with patch('app.main_auth_async.openai_client', mock_async_openai_client):
            response = auth_client.get("/api/v1/rag/diagnose?symptoms=depression+anxiety")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "ai_response" in data
            assert "query" in data
    
    @pytest.mark.asyncio
    async def test_treatment_recommendations_no_openai(self, auth_client):
        """Test treatment recommendations without OpenAI."""
        with patch('app.main_auth_async.openai_client', None):
            response = auth_client.get("/api/v1/rag/treatment?diagnosis=depression")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "error"
            assert "OpenAI service not available" in data["message"]
    
    @pytest.mark.asyncio
    async def test_treatment_recommendations_with_openai(self, auth_client, mock_async_openai_client):
        """Test treatment recommendations with OpenAI."""
        with patch('app.main_auth_async.openai_client', mock_async_openai_client):
            response = auth_client.get("/api/v1/rag/treatment?diagnosis=Major+Depressive+Disorder")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "ai_response" in data
            assert "query" in data
    
    @pytest.mark.asyncio
    async def test_case_analysis_not_found(self, auth_client):
        """Test case analysis with non-existent case."""
        response = auth_client.get("/api/v1/case-analysis/NONEXISTENT")
        assert response.status_code == 404


@pytest.mark.unit
@pytest.mark.auth
class TestAuthenticationUtilities:
    """Test cases for authentication utility functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert verify_password(password, hashed)
    
    def test_verify_password_success(self):
        """Test password verification success."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_verify_password_failure(self):
        """Test password verification failure."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert not verify_password(wrong_password, hashed)
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Test token can be decoded
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
    
    def test_create_access_token_with_expiration(self):
        """Test JWT token creation with custom expiration."""
        from datetime import timedelta
        
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
    
    def test_decode_token_success(self):
        """Test JWT token decoding success."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_token_invalid(self):
        """Test JWT token decoding with invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = decode_token(invalid_token)
        assert payload is None
    
    def test_decode_token_expired(self):
        """Test JWT token decoding with expired token."""
        from datetime import timedelta
        
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta)
        
        payload = decode_token(token)
        assert payload is None
    
    def test_validate_password_strength_success(self):
        """Test password strength validation success."""
        strong_password = "StrongPass123!"
        
        result = validate_password_strength(strong_password)
        assert result == strong_password
    
    def test_validate_password_strength_too_short(self):
        """Test password strength validation - too short."""
        short_password = "Sh0rt!"
        
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password_strength(short_password)
    
    def test_validate_password_strength_too_long(self):
        """Test password strength validation - too long."""
        long_password = "A" * 129 + "1!"
        
        with pytest.raises(ValueError, match="less than 128 characters"):
            validate_password_strength(long_password)
    
    def test_validate_password_strength_no_lowercase(self):
        """Test password strength validation - no lowercase."""
        no_lower = "PASSWORD123!"
        
        with pytest.raises(ValueError, match="lowercase letter"):
            validate_password_strength(no_lower)
    
    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation - no uppercase."""
        no_upper = "password123!"
        
        with pytest.raises(ValueError, match="uppercase letter"):
            validate_password_strength(no_upper)
    
    def test_validate_password_strength_no_digit(self):
        """Test password strength validation - no digit."""
        no_digit = "Password!"
        
        with pytest.raises(ValueError, match="digit"):
            validate_password_strength(no_digit)
    
    def test_validate_password_strength_no_special(self):
        """Test password strength validation - no special character."""
        no_special = "Password123"
        
        with pytest.raises(ValueError, match="special character"):
            validate_password_strength(no_special)


@pytest.mark.unit
@pytest.mark.auth
class TestPydanticModels:
    """Test cases for Pydantic models."""
    
    def test_login_request_model(self):
        """Test LoginRequest model."""
        from app.main_auth_async import LoginRequest
        
        data = {
            "username": "test@example.com",
            "password": "password123"
        }
        
        request = LoginRequest(**data)
        assert request.username == "test@example.com"
        assert request.password == "password123"
    
    def test_registration_request_model(self):
        """Test RegistrationRequest model."""
        from app.main_auth_async import RegistrationRequest
        
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        request = RegistrationRequest(**data)
        assert request.username == "testuser"
        assert request.email == "test@example.com"
        assert request.password == "StrongPass123!"
        assert request.first_name == "Test"
        assert request.last_name == "User"
    
    def test_registration_request_weak_password(self):
        """Test RegistrationRequest with weak password."""
        from app.main_auth_async import RegistrationRequest
        
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User"
        }
        
        with pytest.raises(ValueError):
            RegistrationRequest(**data)
    
    def test_diagnostic_request_model(self):
        """Test DiagnosticRequest model."""
        from app.main_auth_async import DiagnosticRequest
        
        data = {
            "symptoms": "Patient reports feeling sad",
            "patient_context": "29-year-old teacher"
        }
        
        request = DiagnosticRequest(**data)
        assert request.symptoms == "Patient reports feeling sad"
        assert request.patient_context == "29-year-old teacher"
    
    def test_diagnostic_response_model(self):
        """Test DiagnosticResponse model."""
        from app.main_auth_async import DiagnosticResponse
        
        data = {
            "status": "success",
            "ai_response": {"response": "Test response"},
            "query": {"symptoms": "test symptoms"}
        }
        
        response = DiagnosticResponse(**data)
        assert response.status == "success"
        assert response.ai_response == {"response": "Test response"}
        assert response.query == {"symptoms": "test symptoms"}
    
    def test_treatment_request_model(self):
        """Test TreatmentRequest model."""
        from app.main_auth_async import TreatmentRequest
        
        data = {
            "diagnosis": "Major Depressive Disorder",
            "patient_context": "Patient responds well to CBT"
        }
        
        request = TreatmentRequest(**data)
        assert request.diagnosis == "Major Depressive Disorder"
        assert request.patient_context == "Patient responds well to CBT"
    
    def test_treatment_response_model(self):
        """Test TreatmentResponse model."""
        from app.main_auth_async import TreatmentResponse
        
        data = {
            "status": "success",
            "ai_response": {"response": "Treatment recommendations"},
            "query": {"diagnosis": "depression"}
        }
        
        response = TreatmentResponse(**data)
        assert response.status == "success"
        assert response.ai_response == {"response": "Treatment recommendations"}
        assert response.query == {"diagnosis": "depression"}