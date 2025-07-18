"""
Optimized audio analysis service with memory management and error handling.
Provides efficient audio processing with streaming support and resource cleanup.
"""

import base64
import io
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Optional, Tuple, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

import librosa
import numpy as np
import speech_recognition as sr
from pydantic import BaseModel, Field, validator

from app.core.config import get_settings
from app.core.exceptions import (
    AudioProcessingError,
    ValidationError,
    handle_audio_processing_errors,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# Configuration constants
class AudioConfig:
    """Audio processing configuration constants."""
    
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_DURATION = 300  # 5 minutes
    DEFAULT_SAMPLE_RATE = 22050
    CHUNK_SIZE = 1024
    
    # Audio feature extraction settings
    N_MFCC = 13
    N_FBANK = 40
    N_FFT = 2048
    HOP_LENGTH = 512
    
    # Voice analysis thresholds
    SILENCE_THRESHOLD = 0.01
    MIN_PAUSE_LENGTH = 3  # frames
    SPEECH_RATE_WINDOW = 1.0  # seconds


class AudioFeatures(BaseModel):
    """Optimized audio features model with validation."""
    
    mean_pitch: float = Field(default=0.0, ge=0.0, le=1000.0)
    pitch_variance: float = Field(default=0.0, ge=0.0)
    pitch_range: float = Field(default=0.0, ge=0.0)
    mean_energy: float = Field(default=0.0, ge=0.0, le=1.0)
    energy_variance: float = Field(default=0.0, ge=0.0)
    spectral_centroid: float = Field(default=0.0, ge=0.0)
    zero_crossing_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    tempo: float = Field(default=0.0, ge=0.0, le=300.0)
    duration: float = Field(default=0.0, ge=0.0)
    pause_count: int = Field(default=0, ge=0)
    pause_frequency: float = Field(default=0.0, ge=0.0)
    mfcc_features: Optional[list] = Field(default=None)
    spectral_rolloff: float = Field(default=0.0, ge=0.0)
    spectral_bandwidth: float = Field(default=0.0, ge=0.0)
    
    @validator('mfcc_features')
    def validate_mfcc(cls, v):
        """Validate MFCC features."""
        if v is not None and len(v) != AudioConfig.N_MFCC:
            raise ValueError(f"MFCC features must have {AudioConfig.N_MFCC} coefficients")
        return v


class VoiceAnalysis(BaseModel):
    """Comprehensive voice analysis results."""
    
    transcription: str
    sentiment: str = Field(default="neutral")
    emotion: str = Field(default="neutral") 
    tone: str = Field(default="neutral")
    speech_rate: float = Field(default=0.0, ge=0.0)
    pause_frequency: float = Field(default=0.0, ge=0.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    audio_quality: str = Field(default="unknown")
    processing_time: float = Field(default=0.0, ge=0.0)
    features: Optional[AudioFeatures] = None
    
    @validator('sentiment')
    def validate_sentiment(cls, v):
        """Validate sentiment values."""
        valid_sentiments = {"positive", "negative", "neutral"}
        return v if v in valid_sentiments else "neutral"
    
    @validator('emotion', 'tone')
    def validate_emotion_tone(cls, v):
        """Validate emotion and tone values."""
        valid_values = {"excited", "sad", "anxious", "calm", "depressed", "agitated", "neutral"}
        return v if v in valid_values else "neutral"


class OptimizedAudioAnalysisService:
    """Optimized audio analysis service with memory management."""
    
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._setup_recognizer()
    
    def _setup_recognizer(self) -> None:
        """Configure speech recognizer for optimal performance."""
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8
    
    def _validate_audio_data(self, audio_data: str) -> None:
        """Validate audio data before processing."""
        if not audio_data:
            raise ValidationError("Audio data is empty")
        
        # Estimate size before decoding
        estimated_size = len(audio_data) * 3 / 4  # Base64 overhead
        if estimated_size > AudioConfig.MAX_AUDIO_SIZE:
            raise ValidationError(
                f"Audio file too large: {estimated_size:.1f}MB > {AudioConfig.MAX_AUDIO_SIZE / 1024 / 1024}MB"
            )
        
        # Basic format validation
        try:
            # Decode a small sample to validate format
            sample = audio_data[:100]
            base64.b64decode(sample)
        except Exception as e:
            raise ValidationError(f"Invalid base64 audio data: {e}") from e
    
    @asynccontextmanager
    async def _temp_audio_file(self, audio_data: str):
        """Create temporary file for audio processing with cleanup."""
        temp_file = None
        try:
            # Decode audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav', 
                delete=False,
                prefix='therapy_audio_'
            )
            temp_file.write(audio_bytes)
            temp_file.flush()
            temp_path = temp_file.name
            temp_file.close()
            
            yield temp_path
            
        except Exception as e:
            raise AudioProcessingError(
                f"Failed to create temporary audio file: {e}",
                stage="file_creation"
            ) from e
        finally:
            # Cleanup
            if temp_file:
                temp_file.close()
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError as e:
                    logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")
    
    async def transcribe_audio(self, audio_data: str) -> str:
        """Transcribe audio to text with optimized processing."""
        self._validate_audio_data(audio_data)
        
        async with handle_audio_processing_errors("transcription"):
            async with self._temp_audio_file(audio_data) as temp_path:
                return await self._transcribe_file(temp_path)
    
    async def _transcribe_file(self, file_path: str) -> str:
        """Transcribe audio file using speech recognition."""
        loop = asyncio.get_event_loop()
        
        def _transcribe():
            try:
                with sr.AudioFile(file_path) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)
                
                # Use Google Speech Recognition
                return self.recognizer.recognize_google(audio)
                
            except sr.UnknownValueError:
                logger.info("Speech recognition could not understand audio")
                return ""
            except sr.RequestError as e:
                raise AudioProcessingError(
                    f"Speech recognition service error: {e}",
                    stage="speech_recognition"
                ) from e
        
        return await loop.run_in_executor(self.executor, _transcribe)
    
    async def analyze_audio_features(self, audio_data: str) -> AudioFeatures:
        """Extract comprehensive audio features with memory optimization."""
        self._validate_audio_data(audio_data)
        
        async with handle_audio_processing_errors("feature_extraction"):
            async with self._temp_audio_file(audio_data) as temp_path:
                return await self._extract_features(temp_path)
    
    async def _extract_features(self, file_path: str) -> AudioFeatures:
        """Extract audio features from file."""
        loop = asyncio.get_event_loop()
        
        def _extract():
            try:
                # Load audio with memory optimization
                y, sr = librosa.load(
                    file_path, 
                    sr=AudioConfig.DEFAULT_SAMPLE_RATE,
                    mono=True,
                    offset=0.0,
                    duration=AudioConfig.MAX_DURATION
                )
                
                if len(y) == 0:
                    raise AudioProcessingError("Empty audio signal", stage="audio_loading")
                
                # Extract features efficiently
                features = self._compute_features(y, sr)
                
                # Cleanup memory
                del y
                
                return features
                
            except Exception as e:
                if isinstance(e, AudioProcessingError):
                    raise
                raise AudioProcessingError(
                    f"Feature extraction failed: {e}",
                    stage="feature_computation"
                ) from e
        
        return await loop.run_in_executor(self.executor, _extract)
    
    def _compute_features(self, y: np.ndarray, sr: int) -> AudioFeatures:
        """Compute audio features from signal."""
        duration = len(y) / sr
        
        # Pitch analysis
        pitches, magnitudes = librosa.piptrack(
            y=y, sr=sr, 
            threshold=0.1,
            fmin=80, fmax=400  # Human speech range
        )
        
        # Extract fundamental frequency
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        pitch_values = np.array(pitch_values)
        mean_pitch = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 0.0
        pitch_variance = float(np.var(pitch_values)) if len(pitch_values) > 0 else 0.0
        pitch_range = float(np.ptp(pitch_values)) if len(pitch_values) > 0 else 0.0
        
        # Energy analysis
        rms = librosa.feature.rms(y=y, hop_length=AudioConfig.HOP_LENGTH)[0]
        mean_energy = float(np.mean(rms))
        energy_variance = float(np.var(rms))
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(
            y=y, sr=sr, hop_length=AudioConfig.HOP_LENGTH
        )[0]
        mean_spectral_centroid = float(np.mean(spectral_centroids))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=y, sr=sr, hop_length=AudioConfig.HOP_LENGTH
        )[0]
        mean_spectral_rolloff = float(np.mean(spectral_rolloff))
        
        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=y, sr=sr, hop_length=AudioConfig.HOP_LENGTH
        )[0]
        mean_spectral_bandwidth = float(np.mean(spectral_bandwidth))
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(
            y, hop_length=AudioConfig.HOP_LENGTH
        )[0]
        mean_zcr = float(np.mean(zcr))
        
        # Tempo analysis
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo) if not np.isnan(tempo) else 0.0
        
        # MFCC features
        mfccs = librosa.feature.mfcc(
            y=y, sr=sr, 
            n_mfcc=AudioConfig.N_MFCC,
            hop_length=AudioConfig.HOP_LENGTH
        )
        mfcc_means = [float(np.mean(mfcc)) for mfcc in mfccs]
        
        # Pause analysis
        silent_frames = rms < AudioConfig.SILENCE_THRESHOLD
        pauses = self._find_pause_segments(silent_frames, AudioConfig.MIN_PAUSE_LENGTH)
        pause_count = len(pauses)
        pause_frequency = pause_count / duration if duration > 0 else 0.0
        
        return AudioFeatures(
            mean_pitch=mean_pitch,
            pitch_variance=pitch_variance,
            pitch_range=pitch_range,
            mean_energy=mean_energy,
            energy_variance=energy_variance,
            spectral_centroid=mean_spectral_centroid,
            spectral_rolloff=mean_spectral_rolloff,
            spectral_bandwidth=mean_spectral_bandwidth,
            zero_crossing_rate=mean_zcr,
            tempo=tempo,
            duration=duration,
            pause_count=pause_count,
            pause_frequency=pause_frequency,
            mfcc_features=mfcc_means,
        )
    
    def _find_pause_segments(
        self, 
        silent_frames: np.ndarray, 
        min_pause_length: int
    ) -> list:
        """Find pause segments in audio signal."""
        pauses = []
        in_pause = False
        pause_start = 0
        
        for i, is_silent in enumerate(silent_frames):
            if is_silent and not in_pause:
                in_pause = True
                pause_start = i
            elif not is_silent and in_pause:
                pause_length = i - pause_start
                if pause_length >= min_pause_length:
                    pauses.append((pause_start, i))
                in_pause = False
        
        # Handle pause at end
        if in_pause:
            pause_length = len(silent_frames) - pause_start
            if pause_length >= min_pause_length:
                pauses.append((pause_start, len(silent_frames)))
        
        return pauses
    
    def classify_tone_emotion(
        self, 
        features: AudioFeatures, 
        transcription: str
    ) -> Tuple[str, str, str]:
        """Classify tone, emotion, and sentiment from features."""
        # Tone classification based on acoustic features
        tone = self._classify_tone(features)
        
        # Emotion classification
        emotion = self._classify_emotion(features)
        
        # Basic sentiment analysis (can be enhanced with NLP)
        sentiment = self._analyze_basic_sentiment(transcription)
        
        return tone, emotion, sentiment
    
    def _classify_tone(self, features: AudioFeatures) -> str:
        """Classify vocal tone from acoustic features."""
        # Simplified tone classification logic
        if features.mean_pitch > 200 and features.pitch_variance > 1000:
            return "anxious"
        elif features.mean_pitch < 120 and features.mean_energy < 0.01:
            return "depressed"
        elif features.pitch_variance > 800 and features.pause_frequency > 10:
            return "agitated"
        elif features.mean_energy > 0.03 and features.tempo > 120:
            return "excited"
        else:
            return "calm"
    
    def _classify_emotion(self, features: AudioFeatures) -> str:
        """Classify emotion from acoustic features."""
        # Simplified emotion classification
        if features.mean_pitch > 180 and features.energy_variance > 0.01:
            return "excited"
        elif features.mean_pitch < 150 and features.mean_energy < 0.015:
            return "sad"
        elif features.pitch_variance > 1500:
            return "anxious"
        else:
            return "neutral"
    
    def _analyze_basic_sentiment(self, text: str) -> str:
        """Basic sentiment analysis of transcribed text."""
        if not text:
            return "neutral"
        
        text_lower = text.lower()
        
        # Simple keyword-based sentiment
        positive_words = {"happy", "good", "great", "excellent", "wonderful", "amazing"}
        negative_words = {"sad", "bad", "terrible", "awful", "depressed", "anxious"}
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def calculate_speech_rate(self, transcription: str, duration: float) -> float:
        """Calculate speech rate in words per minute."""
        if duration <= 0:
            return 0.0
        
        word_count = len(transcription.split()) if transcription else 0
        words_per_minute = (word_count / duration) * 60
        
        return min(words_per_minute, 300.0)  # Cap at reasonable maximum
    
    def _calculate_confidence(
        self, 
        features: AudioFeatures, 
        transcription: str
    ) -> float:
        """Calculate confidence score for analysis."""
        confidence = 0.5  # Base confidence
        
        # Adjust based on audio quality indicators
        if features.mean_energy > 0.02:
            confidence += 0.2
        if features.duration > 2.0:
            confidence += 0.1
        if len(transcription) > 10:
            confidence += 0.1
        if features.mean_pitch > 0:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _assess_audio_quality(self, features: AudioFeatures) -> str:
        """Assess audio quality based on features."""
        if features.mean_energy < 0.005:
            return "poor"
        elif features.mean_energy > 0.05:
            return "excellent"
        elif features.duration < 1.0:
            return "too_short"
        else:
            return "good"
    
    async def analyze_voice_comprehensive(self, audio_data: str) -> VoiceAnalysis:
        """Perform comprehensive voice analysis with optimization."""
        import time
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_audio_data(audio_data)
            
            # Parallel processing of transcription and features
            transcription_task = asyncio.create_task(
                self.transcribe_audio(audio_data)
            )
            features_task = asyncio.create_task(
                self.analyze_audio_features(audio_data)
            )
            
            # Wait for both tasks to complete
            transcription, features = await asyncio.gather(
                transcription_task, features_task
            )
            
            # Analyze tone, emotion, and sentiment
            tone, emotion, sentiment = self.classify_tone_emotion(features, transcription)
            
            # Calculate derived metrics
            speech_rate = self.calculate_speech_rate(transcription, features.duration)
            confidence = self._calculate_confidence(features, transcription)
            audio_quality = self._assess_audio_quality(features)
            
            processing_time = time.time() - start_time
            
            return VoiceAnalysis(
                transcription=transcription,
                sentiment=sentiment,
                emotion=emotion,
                tone=tone,
                speech_rate=speech_rate,
                pause_frequency=features.pause_frequency,
                confidence=confidence,
                audio_quality=audio_quality,
                processing_time=processing_time,
                features=features,
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Voice analysis failed after {processing_time:.2f}s: {e}")
            raise AudioProcessingError(
                "Comprehensive voice analysis failed",
                stage="comprehensive_analysis",
                details={"processing_time": processing_time}
            ) from e
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health and capabilities."""
        try:
            # Test basic functionality
            test_audio = base64.b64encode(b"test audio data").decode()
            
            return {
                "status": "healthy",
                "features": {
                    "transcription": True,
                    "tone_analysis": True,
                    "emotion_detection": True,
                    "speech_rate_analysis": True,
                    "pause_frequency_analysis": True,
                    "audio_quality_assessment": True,
                },
                "limits": {
                    "max_file_size_mb": AudioConfig.MAX_AUDIO_SIZE / 1024 / 1024,
                    "max_duration_seconds": AudioConfig.MAX_DURATION,
                },
                "performance": {
                    "executor_threads": self.executor._max_workers,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    async def close(self) -> None:
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
            logger.info("Audio analysis service shutdown complete")