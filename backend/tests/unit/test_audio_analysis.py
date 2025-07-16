# Unit tests for audio analysis service

import pytest
from unittest.mock import Mock, patch, MagicMock
import base64
import numpy as np
from fastapi import HTTPException

from app.services.audio_analysis import (
    AudioAnalysisService,
    AudioFeatures,
    VoiceAnalysis
)


@pytest.mark.unit
@pytest.mark.voice
class TestAudioAnalysisService:
    """Test cases for AudioAnalysisService."""
    
    def test_init(self):
        """Test service initialization."""
        service = AudioAnalysisService()
        assert service.recognizer is not None
        assert hasattr(service, 'openai_client')
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, mock_speech_recognizer, sample_audio_data):
        """Test successful audio transcription."""
        service = AudioAnalysisService()
        service.recognizer = mock_speech_recognizer
        
        with patch('app.services.audio_analysis.sr.AudioFile'):
            result = await service.transcribe_audio(sample_audio_data)
            
            assert result == "This is test audio transcription"
            mock_speech_recognizer.recognize_google.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_unknown_value_error(self, mock_speech_recognizer, sample_audio_data):
        """Test audio transcription with unknown value error."""
        import speech_recognition as sr
        
        service = AudioAnalysisService()
        service.recognizer = mock_speech_recognizer
        mock_speech_recognizer.recognize_google.side_effect = sr.UnknownValueError()
        
        with patch('app.services.audio_analysis.sr.AudioFile'):
            result = await service.transcribe_audio(sample_audio_data)
            
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_request_error(self, mock_speech_recognizer, sample_audio_data):
        """Test audio transcription with request error."""
        import speech_recognition as sr
        
        service = AudioAnalysisService()
        service.recognizer = mock_speech_recognizer
        mock_speech_recognizer.recognize_google.side_effect = sr.RequestError("API error")
        
        with patch('app.services.audio_analysis.sr.AudioFile'):
            with pytest.raises(HTTPException) as exc_info:
                await service.transcribe_audio(sample_audio_data)
            
            assert exc_info.value.status_code == 500
            assert "Speech recognition failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_general_error(self, mock_speech_recognizer, sample_audio_data):
        """Test audio transcription with general error."""
        service = AudioAnalysisService()
        service.recognizer = mock_speech_recognizer
        mock_speech_recognizer.recognize_google.side_effect = Exception("General error")
        
        with patch('app.services.audio_analysis.sr.AudioFile'):
            with pytest.raises(HTTPException) as exc_info:
                await service.transcribe_audio(sample_audio_data)
            
            assert exc_info.value.status_code == 500
            assert "Audio transcription failed" in str(exc_info.value.detail)
    
    def test_analyze_audio_features_success(self, mock_librosa, sample_audio_data):
        """Test successful audio features analysis."""
        service = AudioAnalysisService()
        
        with patch('app.services.audio_analysis.io.BytesIO'):
            result = service.analyze_audio_features(sample_audio_data)
            
            assert isinstance(result, AudioFeatures)
            assert result.mean_pitch > 0
            assert result.mean_energy > 0
            assert result.duration >= 0
    
    def test_analyze_audio_features_error(self, sample_audio_data):
        """Test audio features analysis with error."""
        service = AudioAnalysisService()
        
        with patch('app.services.audio_analysis.librosa.load', side_effect=Exception("Librosa error")):
            result = service.analyze_audio_features(sample_audio_data)
            
            # Should return empty AudioFeatures on error
            assert isinstance(result, AudioFeatures)
            assert result.mean_pitch == 0.0
            assert result.mean_energy == 0.0
    
    def test_find_pause_segments(self):
        """Test pause segment detection."""
        service = AudioAnalysisService()
        
        # Create sample silent frames
        silent_frames = np.array([True, True, True, False, False, True, True, True, True, True])
        
        pauses = service._find_pause_segments(silent_frames, min_pause_length=3)
        
        assert len(pauses) == 2  # Should find 2 pause segments
        assert pauses[0] == (0, 3)  # First pause
        assert pauses[1] == (5, 10)  # Second pause
    
    def test_find_pause_segments_short_pauses(self):
        """Test pause segment detection with short pauses."""
        service = AudioAnalysisService()
        
        # Create sample with short pauses
        silent_frames = np.array([True, True, False, False, True, False])
        
        pauses = service._find_pause_segments(silent_frames, min_pause_length=3)
        
        assert len(pauses) == 0  # No pauses long enough
    
    def test_classify_tone_emotion_high_pitch(self):
        """Test tone and emotion classification with high pitch."""
        service = AudioAnalysisService()
        
        features = AudioFeatures(
            mean_pitch=250.0,
            pitch_variance=500.0,
            mean_energy=0.03,
            energy_variance=0.005,
            pause_frequency=5.0
        )
        
        tone, emotion, sentiment = service.classify_tone_emotion(features, "test transcription")
        
        assert tone == "calm"
        assert emotion == "excited"
        assert sentiment == "neutral"
    
    def test_classify_tone_emotion_low_pitch_low_energy(self):
        """Test tone and emotion classification with low pitch and energy."""
        service = AudioAnalysisService()
        
        features = AudioFeatures(
            mean_pitch=100.0,
            pitch_variance=200.0,
            mean_energy=0.005,
            energy_variance=0.002,
            pause_frequency=3.0
        )
        
        tone, emotion, sentiment = service.classify_tone_emotion(features, "test transcription")
        
        assert tone == "depressed"
        assert emotion == "sad"
        assert sentiment == "neutral"
    
    def test_classify_tone_emotion_agitated(self):
        """Test tone and emotion classification for agitated state."""
        service = AudioAnalysisService()
        
        features = AudioFeatures(
            mean_pitch=180.0,
            pitch_variance=800.0,
            mean_energy=0.04,
            energy_variance=0.02,
            pause_frequency=15.0
        )
        
        tone, emotion, sentiment = service.classify_tone_emotion(features, "test transcription")
        
        assert tone == "agitated"
        assert emotion == "excited"
        assert sentiment == "neutral"
    
    def test_classify_tone_emotion_anxious(self):
        """Test tone and emotion classification for anxious state."""
        service = AudioAnalysisService()
        
        features = AudioFeatures(
            mean_pitch=220.0,
            pitch_variance=1800.0,
            mean_energy=0.03,
            energy_variance=0.005,
            pause_frequency=8.0
        )
        
        tone, emotion, sentiment = service.classify_tone_emotion(features, "test transcription")
        
        assert tone == "anxious"
        assert emotion == "anxious"
        assert sentiment == "neutral"
    
    def test_classify_tone_emotion_with_openai(self, mock_openai_client):
        """Test tone and emotion classification with OpenAI sentiment analysis."""
        service = AudioAnalysisService()
        service.openai_client = mock_openai_client
        
        features = AudioFeatures(
            mean_pitch=180.0,
            pitch_variance=500.0,
            mean_energy=0.03,
            energy_variance=0.005,
            pause_frequency=5.0
        )
        
        tone, emotion, sentiment = service.classify_tone_emotion(features, "I feel happy today")
        
        assert tone == "neutral"
        assert emotion == "excited"
        assert sentiment == "positive"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_analyze_sentiment_with_ai_success(self, mock_openai_client):
        """Test AI sentiment analysis success."""
        service = AudioAnalysisService()
        service.openai_client = mock_openai_client
        
        result = service._analyze_sentiment_with_ai("I feel great today")
        
        assert result == "positive"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_analyze_sentiment_with_ai_invalid_response(self, mock_openai_client):
        """Test AI sentiment analysis with invalid response."""
        service = AudioAnalysisService()
        service.openai_client = mock_openai_client
        
        # Mock invalid response
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "invalid_sentiment"
        
        result = service._analyze_sentiment_with_ai("test text")
        
        assert result == "neutral"
    
    def test_analyze_sentiment_with_ai_error(self, mock_openai_client):
        """Test AI sentiment analysis with error."""
        service = AudioAnalysisService()
        service.openai_client = mock_openai_client
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API error")
        
        result = service._analyze_sentiment_with_ai("test text")
        
        assert result == "neutral"
    
    def test_calculate_speech_rate(self):
        """Test speech rate calculation."""
        service = AudioAnalysisService()
        
        transcription = "This is a test sentence with eight words"
        duration = 4.0  # 4 seconds
        
        speech_rate = service.calculate_speech_rate(transcription, duration)
        
        # 8 words in 4 seconds = 2 words per second = 120 words per minute
        assert speech_rate == 120.0
    
    def test_calculate_speech_rate_zero_duration(self):
        """Test speech rate calculation with zero duration."""
        service = AudioAnalysisService()
        
        transcription = "This is a test"
        duration = 0.0
        
        speech_rate = service.calculate_speech_rate(transcription, duration)
        
        assert speech_rate == 0.0
    
    def test_calculate_speech_rate_negative_duration(self):
        """Test speech rate calculation with negative duration."""
        service = AudioAnalysisService()
        
        transcription = "This is a test"
        duration = -1.0
        
        speech_rate = service.calculate_speech_rate(transcription, duration)
        
        assert speech_rate == 0.0
    
    def test_calculate_confidence_high(self):
        """Test confidence calculation with high confidence indicators."""
        service = AudioAnalysisService()
        
        features = AudioFeatures(
            mean_energy=0.05,
            duration=10.0
        )
        transcription = "This is a long transcription with many words to indicate good quality"
        
        confidence = service._calculate_confidence(features, transcription)
        
        assert confidence >= 0.8  # High confidence
    
    def test_calculate_confidence_low(self):
        """Test confidence calculation with low confidence indicators."""
        service = AudioAnalysisService()
        
        features = AudioFeatures(
            mean_energy=0.005,
            duration=1.0
        )
        transcription = "Short"
        
        confidence = service._calculate_confidence(features, transcription)
        
        assert confidence <= 0.7  # Lower confidence
    
    def test_calculate_confidence_max_cap(self):
        """Test confidence calculation doesn't exceed 1.0."""
        service = AudioAnalysisService()
        
        features = AudioFeatures(
            mean_energy=0.1,
            duration=30.0
        )
        transcription = "This is a very long transcription with many words to indicate excellent quality and high confidence"
        
        confidence = service._calculate_confidence(features, transcription)
        
        assert confidence <= 1.0  # Should not exceed 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_voice_comprehensive_success(self, mock_speech_recognizer, mock_librosa, sample_audio_data):
        """Test comprehensive voice analysis success."""
        service = AudioAnalysisService()
        service.recognizer = mock_speech_recognizer
        
        with patch('app.services.audio_analysis.sr.AudioFile'), \
             patch('app.services.audio_analysis.io.BytesIO'):
            
            result = await service.analyze_voice_comprehensive(sample_audio_data)
            
            assert isinstance(result, VoiceAnalysis)
            assert result.transcription == "This is test audio transcription"
            assert result.sentiment in ["positive", "negative", "neutral"]
            assert result.tone in ["calm", "anxious", "depressed", "agitated", "neutral"]
            assert result.emotion in ["excited", "sad", "anxious", "neutral"]
            assert result.speech_rate >= 0
            assert result.pause_frequency >= 0
            assert 0 <= result.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_voice_comprehensive_error(self, mock_speech_recognizer, sample_audio_data):
        """Test comprehensive voice analysis with error."""
        service = AudioAnalysisService()
        service.recognizer = mock_speech_recognizer
        
        # Mock transcription error
        mock_speech_recognizer.recognize_google.side_effect = Exception("Transcription error")
        
        with patch('app.services.audio_analysis.sr.AudioFile'):
            with pytest.raises(HTTPException) as exc_info:
                await service.analyze_voice_comprehensive(sample_audio_data)
            
            assert exc_info.value.status_code == 500
            assert "Voice analysis failed" in str(exc_info.value.detail)


@pytest.mark.unit
@pytest.mark.voice
class TestAudioFeaturesModel:
    """Test cases for AudioFeatures Pydantic model."""
    
    def test_audio_features_creation(self):
        """Test AudioFeatures model creation."""
        features = AudioFeatures(
            mean_pitch=150.0,
            pitch_variance=100.0,
            pitch_range=50.0,
            mean_energy=0.02,
            energy_variance=0.01,
            spectral_centroid=1000.0,
            zero_crossing_rate=0.01,
            tempo=120.0,
            duration=5.0,
            pause_count=3,
            pause_frequency=2.5
        )
        
        assert features.mean_pitch == 150.0
        assert features.pitch_variance == 100.0
        assert features.pitch_range == 50.0
        assert features.mean_energy == 0.02
        assert features.energy_variance == 0.01
        assert features.spectral_centroid == 1000.0
        assert features.zero_crossing_rate == 0.01
        assert features.tempo == 120.0
        assert features.duration == 5.0
        assert features.pause_count == 3
        assert features.pause_frequency == 2.5
    
    def test_audio_features_defaults(self):
        """Test AudioFeatures model with default values."""
        features = AudioFeatures()
        
        assert features.mean_pitch == 0.0
        assert features.pitch_variance == 0.0
        assert features.pitch_range == 0.0
        assert features.mean_energy == 0.0
        assert features.energy_variance == 0.0
        assert features.spectral_centroid == 0.0
        assert features.zero_crossing_rate == 0.0
        assert features.tempo == 0.0
        assert features.duration == 0.0
        assert features.pause_count == 0
        assert features.pause_frequency == 0.0


@pytest.mark.unit
@pytest.mark.voice
class TestVoiceAnalysisModel:
    """Test cases for VoiceAnalysis Pydantic model."""
    
    def test_voice_analysis_creation(self):
        """Test VoiceAnalysis model creation."""
        analysis = VoiceAnalysis(
            transcription="Test transcription",
            sentiment="positive",
            emotion="happy",
            tone="calm",
            speech_rate=120.0,
            pause_frequency=5.0,
            confidence=0.85
        )
        
        assert analysis.transcription == "Test transcription"
        assert analysis.sentiment == "positive"
        assert analysis.emotion == "happy"
        assert analysis.tone == "calm"
        assert analysis.speech_rate == 120.0
        assert analysis.pause_frequency == 5.0
        assert analysis.confidence == 0.85
    
    def test_voice_analysis_sentiment_validation(self):
        """Test VoiceAnalysis sentiment validation."""
        # Valid sentiment
        analysis = VoiceAnalysis(
            transcription="Test",
            sentiment="positive"
        )
        assert analysis.sentiment == "positive"
        
        # Invalid sentiment should be converted to neutral
        analysis = VoiceAnalysis(
            transcription="Test",
            sentiment="invalid_sentiment"
        )
        assert analysis.sentiment == "neutral"
    
    def test_voice_analysis_tone_validation(self):
        """Test VoiceAnalysis tone validation."""
        # Valid tone
        analysis = VoiceAnalysis(
            transcription="Test",
            tone="anxious"
        )
        assert analysis.tone == "anxious"
        
        # Invalid tone should be converted to neutral
        analysis = VoiceAnalysis(
            transcription="Test",
            tone="invalid_tone"
        )
        assert analysis.tone == "neutral"
    
    def test_voice_analysis_confidence_validation(self):
        """Test VoiceAnalysis confidence validation."""
        # Valid confidence
        analysis = VoiceAnalysis(
            transcription="Test",
            confidence=0.75
        )
        assert analysis.confidence == 0.75
        
        # Test confidence bounds are enforced by Pydantic
        with pytest.raises(ValueError):
            VoiceAnalysis(
                transcription="Test",
                confidence=1.5  # Above 1.0
            )
        
        with pytest.raises(ValueError):
            VoiceAnalysis(
                transcription="Test",
                confidence=-0.1  # Below 0.0
            )
    
    def test_voice_analysis_defaults(self):
        """Test VoiceAnalysis model with default values."""
        analysis = VoiceAnalysis(transcription="Test")
        
        assert analysis.transcription == "Test"
        assert analysis.sentiment == "neutral"
        assert analysis.emotion == "neutral"
        assert analysis.tone == "neutral"
        assert analysis.speech_rate == 0.0
        assert analysis.pause_frequency == 0.0
        assert analysis.confidence == 0.0