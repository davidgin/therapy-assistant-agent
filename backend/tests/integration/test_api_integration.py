# Integration tests for API endpoints

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
import asyncio

from app.main_auth_async import (
    User,
    UserRole,
    LicenseType,
    hash_password,
    create_access_token
)
from app.services.audio_analysis import VoiceAnalysis


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationFlow:
    """Integration tests for authentication flow."""
    
    @pytest.mark.asyncio
    async def test_complete_registration_and_login_flow(self, auth_client, async_db):
        """Test complete user registration and login flow."""
        # Step 1: Register new user
        registration_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = auth_client.post("/api/auth/register", json=registration_data)
        assert response.status_code == 200
        
        registration_result = response.json()
        assert registration_result["message"] == "User registered successfully"
        assert registration_result["user"]["email"] == "newuser@example.com"
        
        # Step 2: Login with registered user
        login_data = {
            "username": "newuser@example.com",
            "password": "NewPassword123!"
        }
        
        response = auth_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        login_result = response.json()
        assert "access_token" in login_result
        assert login_result["user"]["email"] == "newuser@example.com"
        
        # Step 3: Access protected endpoint
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        response = auth_client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        user_info = response.json()
        assert user_info["email"] == "newuser@example.com"
    
    @pytest.mark.asyncio
    async def test_authentication_with_different_roles(self, auth_client, async_db):
        """Test authentication with different user roles."""
        # Create users with different roles
        users = [
            {
                "email": "admin@example.com",
                "username": "admin",
                "role": UserRole.ADMIN,
                "password": "AdminPass123!"
            },
            {
                "email": "therapist@example.com",
                "username": "therapist",
                "role": UserRole.THERAPIST,
                "license_type": LicenseType.LMFT,
                "password": "TherapistPass123!"
            },
            {
                "email": "student@example.com",
                "username": "student",
                "role": UserRole.STUDENT,
                "license_type": LicenseType.STUDENT,
                "password": "StudentPass123!"
            }
        ]
        
        for user_data in users:
            # Create user directly in database
            user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=hash_password(user_data["password"]),
                first_name="Test",
                last_name="User",
                role=user_data["role"],
                license_type=user_data.get("license_type", LicenseType.STUDENT),
                is_active=True,
                is_verified=True
            )
            
            async_db.add(user)
            await async_db.commit()
            
            # Test login
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }
            
            response = auth_client.post("/api/auth/login", json=login_data)
            assert response.status_code == 200
            
            result = response.json()
            assert result["user"]["role"] == user_data["role"].value
    
    @pytest.mark.asyncio
    async def test_token_expiration_and_refresh_flow(self, auth_client, test_user):
        """Test token expiration and refresh flow."""
        # Create short-lived token
        short_token = create_access_token(
            data={"sub": test_user.email},
            expires_delta={"seconds": 1}
        )
        
        # Token should work initially
        headers = {"Authorization": f"Bearer {short_token}"}
        response = auth_client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # Token should be expired
        response = auth_client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        
        # Should be able to login again to get new token
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }
        
        response = auth_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        
        # New token should work
        new_headers = {"Authorization": f"Bearer {result['access_token']}"}
        response = auth_client.get("/api/auth/me", headers=new_headers)
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.voice
class TestVoiceAnalysisFlow:
    """Integration tests for voice analysis flow."""
    
    @pytest.mark.asyncio
    async def test_complete_voice_analysis_flow(self, auth_client, test_user, auth_headers, sample_audio_data):
        """Test complete voice analysis flow."""
        # Mock the audio analysis service
        mock_analysis = VoiceAnalysis(
            transcription="I have been feeling very anxious lately",
            sentiment="negative",
            emotion="anxious",
            tone="anxious",
            speech_rate=140.0,
            pause_frequency=12.0,
            confidence=0.88
        )
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.analyze_voice_comprehensive.return_value = mock_analysis
            
            # Step 1: Perform voice analysis
            request_data = {"audio_data": sample_audio_data}
            response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
            assert response.status_code == 200
            
            result = response.json()
            assert result["transcription"] == "I have been feeling very anxious lately"
            assert result["sentiment"] == "negative"
            assert result["emotion"] == "anxious"
            assert result["tone"] == "anxious"
            assert result["speech_rate"] == 140.0
            assert result["pause_frequency"] == 12.0
            assert result["confidence"] == 0.88
            
            # Step 2: Use transcription for diagnostic assistance
            diagnostic_params = f"symptoms={result['transcription']}"
            
            with patch('app.main_auth_async.openai_client') as mock_openai:
                mock_openai.chat.completions.create.return_value.choices[0].message.content = \
                    "Based on the symptoms described, this may indicate anxiety disorder."
                
                response = auth_client.get(f"/api/v1/rag/diagnose?{diagnostic_params}")
                assert response.status_code == 200
                
                diagnostic_result = response.json()
                assert diagnostic_result["status"] == "success"
                assert "anxiety" in diagnostic_result["ai_response"].lower()
    
    @pytest.mark.asyncio
    async def test_voice_analysis_with_treatment_recommendations(self, auth_client, test_user, auth_headers, sample_audio_data):
        """Test voice analysis integrated with treatment recommendations."""
        # Mock voice analysis
        mock_analysis = VoiceAnalysis(
            transcription="I feel depressed and have no energy",
            sentiment="negative",
            emotion="sad",
            tone="depressed",
            speech_rate=90.0,
            pause_frequency=8.0,
            confidence=0.85
        )
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.analyze_voice_comprehensive.return_value = mock_analysis
            
            # Step 1: Analyze voice
            request_data = {"audio_data": sample_audio_data}
            response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
            assert response.status_code == 200
            
            voice_result = response.json()
            
            # Step 2: Get diagnostic suggestions
            with patch('app.main_auth_async.openai_client') as mock_openai:
                mock_openai.chat.completions.create.return_value.choices[0].message.content = \
                    "Major Depressive Disorder"
                
                diagnostic_params = f"symptoms={voice_result['transcription']}"
                response = auth_client.get(f"/api/v1/rag/diagnose?{diagnostic_params}")
                assert response.status_code == 200
                
                diagnostic_result = response.json()
                
                # Step 3: Get treatment recommendations
                mock_openai.chat.completions.create.return_value.choices[0].message.content = \
                    "Recommended treatment includes cognitive behavioral therapy and medication evaluation."
                
                treatment_params = f"diagnosis=Major Depressive Disorder"
                response = auth_client.get(f"/api/v1/rag/treatment?{treatment_params}")
                assert response.status_code == 200
                
                treatment_result = response.json()
                assert treatment_result["status"] == "success"
                assert "cognitive behavioral therapy" in treatment_result["ai_response"].lower()
    
    @pytest.mark.asyncio
    async def test_voice_analysis_error_handling(self, auth_client, test_user, auth_headers, sample_audio_data):
        """Test voice analysis error handling."""
        # Test with audio analysis service failure
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.analyze_voice_comprehensive.side_effect = Exception("Audio processing failed")
            
            request_data = {"audio_data": sample_audio_data}
            response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
            assert response.status_code == 500
            
            # Should handle gracefully
            assert "error" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.web
class TestWebIntegrationFlow:
    """Integration tests for web interface flow."""
    
    @pytest.mark.asyncio
    async def test_complete_web_diagnostic_flow(self, web_client, test_user):
        """Test complete web diagnostic flow."""
        # Step 1: Login via web interface
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }
        
        response = web_client.post("/login", data=login_data, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"
        
        # Get the token from cookies
        token = response.cookies.get("token")
        assert token is not None
        
        # Step 2: Access dashboard
        with patch('app.main_web.get_current_user_required', return_value=test_user):
            response = web_client.get("/dashboard")
            assert response.status_code == 200
            
            # Step 3: Access diagnostic page
            response = web_client.get("/diagnostic")
            assert response.status_code == 200
            
            # Step 4: Submit diagnostic form
            with patch('app.main_web.openai_client') as mock_openai:
                mock_openai.chat.completions.create.return_value.choices[0].message.content = \
                    "Based on the symptoms, this suggests possible anxiety disorder."
                
                diagnostic_data = {
                    "symptoms": "Patient reports persistent worry and restlessness",
                    "patient_context": "30-year-old professional with no prior mental health history"
                }
                
                response = web_client.post("/diagnostic", data=diagnostic_data)
                assert response.status_code == 200
                
                # Should contain diagnostic results
                assert "anxiety" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_web_treatment_flow(self, web_client, test_user):
        """Test web treatment recommendation flow."""
        with patch('app.main_web.get_current_user_required', return_value=test_user):
            # Step 1: Access treatment page
            response = web_client.get("/treatment")
            assert response.status_code == 200
            
            # Step 2: Submit treatment form
            with patch('app.main_web.openai_client') as mock_openai:
                mock_openai.chat.completions.create.return_value.choices[0].message.content = \
                    "Recommended treatment includes CBT and medication evaluation."
                
                treatment_data = {
                    "diagnosis": "Major Depressive Disorder",
                    "patient_context": "Patient responds well to structured interventions"
                }
                
                response = web_client.post("/treatment", data=treatment_data)
                assert response.status_code == 200
                
                # Should contain treatment recommendations
                assert "cbt" in response.text.lower() or "cognitive" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_web_cases_page_flow(self, web_client, test_user):
        """Test web cases page flow."""
        with patch('app.main_web.get_current_user_required', return_value=test_user):
            # Mock synthetic cases
            mock_cases = [
                {
                    "id": "case1",
                    "disorder": "Depression",
                    "symptoms": ["low mood", "fatigue", "loss of interest"],
                    "demographics": {"age": 25, "gender": "female"}
                },
                {
                    "id": "case2",
                    "disorder": "Anxiety",
                    "symptoms": ["worry", "restlessness", "panic attacks"],
                    "demographics": {"age": 32, "gender": "male"}
                }
            ]
            
            with patch('app.services.async_file_service.load_synthetic_cases', return_value=mock_cases):
                response = web_client.get("/cases")
                assert response.status_code == 200
                
                # Should display cases
                assert "depression" in response.text.lower()
                assert "anxiety" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_web_logout_flow(self, web_client, test_user):
        """Test web logout flow."""
        # Login first
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }
        
        response = web_client.post("/login", data=login_data, follow_redirects=False)
        assert response.status_code == 302
        
        # Logout
        response = web_client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
        
        # Token should be cleared
        token = response.cookies.get("token")
        assert token == ""


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.mark.asyncio
    async def test_user_crud_operations(self, async_db):
        """Test complete user CRUD operations."""
        # Create
        user = User(
            email="crud@example.com",
            username="cruduser",
            hashed_password=hash_password("password123"),
            first_name="CRUD",
            last_name="User",
            role=UserRole.THERAPIST,
            license_type=LicenseType.LMFT,
            license_number="CRUD123456",
            license_state="CA",
            is_active=True,
            is_verified=True
        )
        
        async_db.add(user)
        await async_db.commit()
        await async_db.refresh(user)
        
        assert user.id is not None
        created_user_id = user.id
        
        # Read
        from sqlalchemy import select
        result = await async_db.execute(
            select(User).where(User.id == created_user_id)
        )
        retrieved_user = result.scalar_one_or_none()
        
        assert retrieved_user is not None
        assert retrieved_user.email == "crud@example.com"
        assert retrieved_user.username == "cruduser"
        
        # Update
        retrieved_user.first_name = "Updated"
        await async_db.commit()
        await async_db.refresh(retrieved_user)
        
        assert retrieved_user.first_name == "Updated"
        
        # Delete
        await async_db.delete(retrieved_user)
        await async_db.commit()
        
        result = await async_db.execute(
            select(User).where(User.id == created_user_id)
        )
        deleted_user = result.scalar_one_or_none()
        
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_user_relationship_queries(self, async_db):
        """Test user relationship queries."""
        # Create multiple users with different roles
        users = [
            User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                hashed_password=hash_password("password123"),
                first_name=f"User{i}",
                last_name="Test",
                role=UserRole.THERAPIST if i % 2 == 0 else UserRole.STUDENT,
                license_type=LicenseType.LMFT if i % 2 == 0 else LicenseType.STUDENT,
                is_active=True,
                is_verified=True
            ) for i in range(5)
        ]
        
        for user in users:
            async_db.add(user)
        await async_db.commit()
        
        # Query therapists
        from sqlalchemy import select
        result = await async_db.execute(
            select(User).where(User.role == UserRole.THERAPIST)
        )
        therapists = result.scalars().all()
        
        assert len(therapists) == 3  # users 0, 2, 4
        
        # Query students
        result = await async_db.execute(
            select(User).where(User.role == UserRole.STUDENT)
        )
        students = result.scalars().all()
        
        assert len(students) == 2  # users 1, 3
        
        # Query by license type
        result = await async_db.execute(
            select(User).where(User.license_type == LicenseType.LMFT)
        )
        lmft_users = result.scalars().all()
        
        assert len(lmft_users) == 3


@pytest.mark.integration
@pytest.mark.api
class TestAPIEndpointIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_endpoints(self, auth_client):
        """Test health check endpoints."""
        # Auth API health check
        response = auth_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "openai" in data
        
        # Voice API health check
        response = auth_client.get("/voice/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "features" in data
    
    @pytest.mark.asyncio
    async def test_synthetic_cases_endpoint(self, auth_client):
        """Test synthetic cases endpoint."""
        mock_cases = [
            {
                "id": "case1",
                "disorder": "Depression",
                "symptoms": ["sadness", "fatigue"]
            }
        ]
        
        with patch('app.services.async_file_service.load_synthetic_cases', return_value=mock_cases):
            response = auth_client.get("/api/v1/synthetic-cases")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "cases" in data
            assert len(data["cases"]) == 1
    
    @pytest.mark.asyncio
    async def test_rag_diagnostic_endpoint(self, auth_client):
        """Test RAG diagnostic endpoint."""
        with patch('app.main_auth_async.openai_client') as mock_openai:
            mock_openai.chat.completions.create.return_value.choices[0].message.content = \
                "Based on the symptoms, this suggests possible depression."
            
            response = auth_client.get("/api/v1/rag/diagnose?symptoms=feeling+sad+and+tired")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "ai_response" in data
            assert "depression" in data["ai_response"].lower()
    
    @pytest.mark.asyncio
    async def test_rag_treatment_endpoint(self, auth_client):
        """Test RAG treatment endpoint."""
        with patch('app.main_auth_async.openai_client') as mock_openai:
            mock_openai.chat.completions.create.return_value.choices[0].message.content = \
                "Recommended treatment includes therapy and medication evaluation."
            
            response = auth_client.get("/api/v1/rag/treatment?diagnosis=Major+Depressive+Disorder")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "ai_response" in data
            assert "therapy" in data["ai_response"].lower()
    
    @pytest.mark.asyncio
    async def test_case_analysis_endpoint(self, auth_client):
        """Test case analysis endpoint."""
        # Test with non-existent case
        response = auth_client.get("/api/v1/case-analysis/NONEXISTENT")
        assert response.status_code == 404