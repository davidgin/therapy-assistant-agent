# Unit tests for voice analysis endpoints

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
import json
import base64

from app.main_auth_async import (
    VoiceTranscriptionRequest,
    VoiceTranscriptionResponse,
    VoiceAnalysisRequest,
    VoiceAnalysisResponse,
    User,
    UserRole,
    LicenseType
)
from app.services.audio_analysis import VoiceAnalysis, AudioFeatures


@pytest.mark.unit
@pytest.mark.voice
class TestVoiceTranscriptionEndpoint:
    """Test cases for voice transcription endpoint."""
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, auth_client, test_user, auth_headers, sample_audio_data):
        """Test successful audio transcription."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.transcribe_audio.return_value = "This is the transcribed text"
            
            response = auth_client.post(
                "/voice/transcribe", 
                json=request_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["transcription"] == "This is the transcribed text"
            assert data["success"] is True
            
            mock_instance.transcribe_audio.assert_called_once_with(sample_audio_data)
    
    @pytest.mark.asyncio
    async def test_transcribe_unauthorized(self, auth_client, sample_audio_data):
        """Test transcription without authentication."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        response = auth_client.post("/voice/transcribe", json=request_data)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_transcribe_invalid_token(self, auth_client, sample_audio_data):
        """Test transcription with invalid token."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        headers = {"Authorization": "Bearer invalid_token"}
        response = auth_client.post("/voice/transcribe", json=request_data, headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_transcribe_unlicensed_user(self, auth_client, async_db, sample_audio_data):
        """Test transcription with unlicensed user."""
        from app.main_auth_async import hash_password, create_access_token
        
        # Create unlicensed user
        unlicensed_user = User(
            email="unlicensed@example.com",
            username="unlicensed",
            hashed_password=hash_password("password123"),
            first_name="Unlicensed",
            last_name="User",
            role=UserRole.STUDENT,
            license_type=LicenseType.STUDENT,
            is_active=True,
            is_verified=True
        )
        async_db.add(unlicensed_user)
        await async_db.commit()
        
        token = create_access_token(data={"sub": unlicensed_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        request_data = {
            "audio_data": sample_audio_data
        }
        
        response = auth_client.post("/voice/transcribe", json=request_data, headers=headers)
        assert response.status_code == 403
        
        data = response.json()
        assert "not licensed" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_transcribe_missing_audio_data(self, auth_client, auth_headers):
        """Test transcription with missing audio data."""
        request_data = {}
        
        response = auth_client.post("/voice/transcribe", json=request_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_transcribe_empty_audio_data(self, auth_client, auth_headers):
        """Test transcription with empty audio data."""
        request_data = {
            "audio_data": ""
        }
        
        response = auth_client.post("/voice/transcribe", json=request_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_transcribe_invalid_audio_data(self, auth_client, auth_headers):
        """Test transcription with invalid audio data."""
        request_data = {
            "audio_data": "invalid_base64_data"
        }
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.transcribe_audio.side_effect = Exception("Invalid audio format")
            
            response = auth_client.post("/voice/transcribe", json=request_data, headers=auth_headers)
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_transcribe_service_error(self, auth_client, auth_headers, sample_audio_data):
        """Test transcription with service error."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.transcribe_audio.side_effect = Exception("Service unavailable")
            
            response = auth_client.post("/voice/transcribe", json=request_data, headers=auth_headers)
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_transcribe_empty_result(self, auth_client, auth_headers, sample_audio_data):
        """Test transcription with empty result."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.transcribe_audio.return_value = ""
            
            response = auth_client.post("/voice/transcribe", json=request_data, headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["transcription"] == ""
            assert data["success"] is True


@pytest.mark.unit
@pytest.mark.voice
class TestVoiceAnalysisEndpoint:
    """Test cases for voice analysis endpoint."""
    
    @pytest.mark.asyncio
    async def test_analyze_voice_success(self, auth_client, test_user, auth_headers, sample_audio_data):
        """Test successful voice analysis."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        mock_analysis = VoiceAnalysis(
            transcription="I feel anxious about this situation",
            sentiment="negative",
            emotion="anxious",
            tone="anxious",
            speech_rate=150.0,
            pause_frequency=8.5,
            confidence=0.85
        )
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.analyze_voice_comprehensive.return_value = mock_analysis
            
            response = auth_client.post(
                "/voice/analyze", 
                json=request_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["transcription"] == "I feel anxious about this situation"
            assert data["sentiment"] == "negative"
            assert data["emotion"] == "anxious"
            assert data["tone"] == "anxious"
            assert data["speech_rate"] == 150.0
            assert data["pause_frequency"] == 8.5
            assert data["confidence"] == 0.85
            assert data["success"] is True
            
            mock_instance.analyze_voice_comprehensive.assert_called_once_with(sample_audio_data)
    
    @pytest.mark.asyncio
    async def test_analyze_voice_unauthorized(self, auth_client, sample_audio_data):
        """Test voice analysis without authentication."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        response = auth_client.post("/voice/analyze", json=request_data)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_analyze_voice_unlicensed_user(self, auth_client, async_db, sample_audio_data):
        """Test voice analysis with unlicensed user."""
        from app.main_auth_async import hash_password, create_access_token
        
        # Create unlicensed user
        unlicensed_user = User(
            email="unlicensed@example.com",
            username="unlicensed",
            hashed_password=hash_password("password123"),
            first_name="Unlicensed",
            last_name="User",
            role=UserRole.STUDENT,
            license_type=LicenseType.STUDENT,
            is_active=True,
            is_verified=True
        )
        async_db.add(unlicensed_user)
        await async_db.commit()
        
        token = create_access_token(data={"sub": unlicensed_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        request_data = {
            "audio_data": sample_audio_data
        }
        
        response = auth_client.post("/voice/analyze", json=request_data, headers=headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_analyze_voice_missing_audio_data(self, auth_client, auth_headers):
        """Test voice analysis with missing audio data."""
        request_data = {}
        
        response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_analyze_voice_service_error(self, auth_client, auth_headers, sample_audio_data):
        """Test voice analysis with service error."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.analyze_voice_comprehensive.side_effect = Exception("Analysis failed")
            
            response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_analyze_voice_with_different_emotions(self, auth_client, auth_headers, sample_audio_data):
        """Test voice analysis with different emotion results."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        test_cases = [
            {
                "emotion": "sad",
                "tone": "depressed",
                "sentiment": "negative",
                "speech_rate": 80.0
            },
            {
                "emotion": "excited",
                "tone": "agitated",
                "sentiment": "positive",
                "speech_rate": 180.0
            },
            {
                "emotion": "neutral",
                "tone": "calm",
                "sentiment": "neutral",
                "speech_rate": 120.0
            }
        ]
        
        for case in test_cases:
            mock_analysis = VoiceAnalysis(
                transcription="Test transcription",
                sentiment=case["sentiment"],
                emotion=case["emotion"],
                tone=case["tone"],
                speech_rate=case["speech_rate"],
                pause_frequency=5.0,
                confidence=0.75
            )
            
            with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
                mock_instance = mock_service.return_value
                mock_instance.analyze_voice_comprehensive.return_value = mock_analysis
                
                response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
                assert response.status_code == 200
                
                data = response.json()
                assert data["emotion"] == case["emotion"]
                assert data["tone"] == case["tone"]
                assert data["sentiment"] == case["sentiment"]
                assert data["speech_rate"] == case["speech_rate"]
    
    @pytest.mark.asyncio
    async def test_analyze_voice_confidence_levels(self, auth_client, auth_headers, sample_audio_data):
        """Test voice analysis with different confidence levels."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        confidence_levels = [0.3, 0.6, 0.9]
        
        for confidence in confidence_levels:
            mock_analysis = VoiceAnalysis(
                transcription="Test transcription",
                sentiment="neutral",
                emotion="neutral",
                tone="neutral",
                speech_rate=120.0,
                pause_frequency=5.0,
                confidence=confidence
            )
            
            with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
                mock_instance = mock_service.return_value
                mock_instance.analyze_voice_comprehensive.return_value = mock_analysis
                
                response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
                assert response.status_code == 200
                
                data = response.json()
                assert data["confidence"] == confidence
    
    @pytest.mark.asyncio
    async def test_analyze_voice_long_transcription(self, auth_client, auth_headers, sample_audio_data):
        """Test voice analysis with long transcription."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        long_transcription = "This is a very long transcription that contains multiple sentences and should test the system's ability to handle longer audio inputs with more complex content and analysis requirements."
        
        mock_analysis = VoiceAnalysis(
            transcription=long_transcription,
            sentiment="neutral",
            emotion="neutral",
            tone="neutral",
            speech_rate=120.0,
            pause_frequency=5.0,
            confidence=0.8
        )
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.analyze_voice_comprehensive.return_value = mock_analysis
            
            response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["transcription"] == long_transcription
            assert len(data["transcription"]) > 100


@pytest.mark.unit
@pytest.mark.voice
class TestVoiceHealthEndpoint:
    """Test cases for voice health check endpoint."""
    
    def test_voice_health_success(self, auth_client):
        """Test voice health check endpoint."""
        response = auth_client.get("/voice/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "features" in data
        assert "transcription" in data["features"]
        assert "tone_analysis" in data["features"]
        assert "emotion_detection" in data["features"]
        assert "speech_rate_analysis" in data["features"]
        assert "pause_frequency_analysis" in data["features"]
    
    def test_voice_health_service_availability(self, auth_client):
        """Test voice health check with service availability."""
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            # Mock service initialization success
            mock_service.return_value = Mock()
            
            response = auth_client.get("/voice/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "message" in data
    
    def test_voice_health_service_error(self, auth_client):
        """Test voice health check with service error."""
        with patch('app.main_auth_async.AudioAnalysisService', side_effect=Exception("Service error")):
            response = auth_client.get("/voice/health")
            assert response.status_code == 200
            
            data = response.json()
            # Should still return healthy status but indicate service issues
            assert "status" in data


@pytest.mark.unit
@pytest.mark.voice
class TestVoiceRateLimiting:
    """Test cases for voice endpoint rate limiting."""
    
    @pytest.mark.asyncio
    async def test_transcribe_rate_limit(self, auth_client, auth_headers, sample_audio_data):
        """Test transcription rate limiting."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.transcribe_audio.return_value = "Test transcription"
            
            # Make multiple requests to test rate limiting
            for i in range(12):  # Rate limit is 10 per minute
                response = auth_client.post("/voice/transcribe", json=request_data, headers=auth_headers)
                if i < 10:
                    assert response.status_code == 200
                else:
                    # Should be rate limited after 10 requests
                    assert response.status_code == 429
    
    @pytest.mark.asyncio
    async def test_analyze_rate_limit(self, auth_client, auth_headers, sample_audio_data):
        """Test voice analysis rate limiting."""
        request_data = {
            "audio_data": sample_audio_data
        }
        
        mock_analysis = VoiceAnalysis(
            transcription="Test",
            sentiment="neutral",
            emotion="neutral",
            tone="neutral",
            speech_rate=120.0,
            pause_frequency=5.0,
            confidence=0.8
        )
        
        with patch('app.main_auth_async.AudioAnalysisService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.analyze_voice_comprehensive.return_value = mock_analysis
            
            # Make multiple requests to test rate limiting
            for i in range(12):  # Rate limit is 10 per minute
                response = auth_client.post("/voice/analyze", json=request_data, headers=auth_headers)
                if i < 10:
                    assert response.status_code == 200
                else:
                    # Should be rate limited after 10 requests
                    assert response.status_code == 429


@pytest.mark.unit
@pytest.mark.voice
class TestVoiceRequestModels:
    """Test cases for voice request Pydantic models."""
    
    def test_voice_transcription_request_model(self, sample_audio_data):
        """Test VoiceTranscriptionRequest model."""
        request = VoiceTranscriptionRequest(audio_data=sample_audio_data)
        assert request.audio_data == sample_audio_data
    
    def test_voice_transcription_request_validation(self):
        """Test VoiceTranscriptionRequest validation."""
        with pytest.raises(ValueError):
            VoiceTranscriptionRequest(audio_data="")
        
        with pytest.raises(ValueError):
            VoiceTranscriptionRequest(audio_data=None)
    
    def test_voice_analysis_request_model(self, sample_audio_data):
        """Test VoiceAnalysisRequest model."""
        request = VoiceAnalysisRequest(audio_data=sample_audio_data)
        assert request.audio_data == sample_audio_data
    
    def test_voice_analysis_request_validation(self):
        """Test VoiceAnalysisRequest validation."""
        with pytest.raises(ValueError):
            VoiceAnalysisRequest(audio_data="")
        
        with pytest.raises(ValueError):
            VoiceAnalysisRequest(audio_data=None)


@pytest.mark.unit
@pytest.mark.voice
class TestVoiceResponseModels:
    """Test cases for voice response Pydantic models."""
    
    def test_voice_transcription_response_model(self):
        """Test VoiceTranscriptionResponse model."""
        response = VoiceTranscriptionResponse(
            transcription="Test transcription",
            success=True
        )
        assert response.transcription == "Test transcription"
        assert response.success is True
    
    def test_voice_analysis_response_model(self):
        """Test VoiceAnalysisResponse model."""
        response = VoiceAnalysisResponse(
            transcription="Test transcription",
            sentiment="positive",
            emotion="happy",
            tone="calm",
            speech_rate=120.0,
            pause_frequency=5.0,
            confidence=0.85,
            success=True
        )
        
        assert response.transcription == "Test transcription"
        assert response.sentiment == "positive"
        assert response.emotion == "happy"
        assert response.tone == "calm"
        assert response.speech_rate == 120.0
        assert response.pause_frequency == 5.0
        assert response.confidence == 0.85
        assert response.success is True
    
    def test_voice_analysis_response_defaults(self):
        """Test VoiceAnalysisResponse with default values."""
        response = VoiceAnalysisResponse(
            transcription="Test",
            success=True
        )
        
        assert response.transcription == "Test"
        assert response.sentiment == "neutral"
        assert response.emotion == "neutral"
        assert response.tone == "neutral"
        assert response.speech_rate == 0.0
        assert response.pause_frequency == 0.0
        assert response.confidence == 0.0
        assert response.success is True