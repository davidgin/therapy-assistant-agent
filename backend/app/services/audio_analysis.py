"""
Audio analysis service for voice tone and emotion detection
"""

import io
import base64
import json
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import speech_recognition as sr
import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram
import librosa
import openai
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException
from ..core.config import settings

logger = logging.getLogger(__name__)

class AudioFeatures(BaseModel):
    """Audio features extracted from speech signal"""
    mean_pitch: float = Field(default=0.0, description="Mean fundamental frequency")
    pitch_variance: float = Field(default=0.0, description="Pitch variance")
    pitch_range: float = Field(default=0.0, description="Pitch range (max - min)")
    mean_energy: float = Field(default=0.0, description="Mean RMS energy")
    energy_variance: float = Field(default=0.0, description="Energy variance")
    spectral_centroid: float = Field(default=0.0, description="Spectral centroid")
    zero_crossing_rate: float = Field(default=0.0, description="Zero crossing rate")
    tempo: float = Field(default=0.0, description="Estimated tempo")
    duration: float = Field(default=0.0, description="Audio duration in seconds")
    pause_count: int = Field(default=0, description="Number of detected pauses")
    pause_frequency: float = Field(default=0.0, description="Pauses per minute")

class VoiceAnalysis(BaseModel):
    """Complete voice analysis results"""
    transcription: str = Field(..., description="Transcribed text from speech")
    sentiment: str = Field(default="neutral", description="Sentiment classification")
    emotion: str = Field(default="neutral", description="Detected emotion")
    tone: str = Field(default="neutral", description="Voice tone classification")
    speech_rate: float = Field(default=0.0, description="Words per minute")
    pause_frequency: float = Field(default=0.0, description="Pauses per minute")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Analysis confidence score")
    
    @validator('sentiment')
    def validate_sentiment(cls, v: str) -> str:
        allowed_sentiments = ['positive', 'negative', 'neutral']
        if v not in allowed_sentiments:
            return 'neutral'
        return v
    
    @validator('tone')
    def validate_tone(cls, v: str) -> str:
        allowed_tones = ['calm', 'anxious', 'depressed', 'agitated', 'neutral']
        if v not in allowed_tones:
            return 'neutral'
        return v

class AudioAnalysisService:
    """Service for analyzing audio files for transcription and emotional content"""
    
    def __init__(self) -> None:
        self.recognizer: sr.Recognizer = sr.Recognizer()
        self.openai_client: Optional[openai.OpenAI] = (
            openai.OpenAI(api_key=settings.OPENAI_API_KEY) 
            if settings.OPENAI_API_KEY else None
        )
        
    async def transcribe_audio(self, audio_data: str) -> str:
        """Transcribe audio to text using speech recognition"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Create audio file object
            audio_file = io.BytesIO(audio_bytes)
            
            # Use speech recognition
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                
            # Perform recognition
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            raise HTTPException(status_code=500, detail="Speech recognition failed")
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise HTTPException(status_code=500, detail="Audio transcription failed")
    
    def analyze_audio_features(self, audio_data: str) -> AudioFeatures:
        """Analyze audio features for tone and emotion detection"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Load audio with librosa
            audio_array, sample_rate = librosa.load(io.BytesIO(audio_bytes), sr=None)
            
            # Extract features
            # Fundamental frequency (pitch)
            pitches, magnitudes = librosa.piptrack(y=audio_array, sr=sample_rate)
            pitch_values: List[float] = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(float(pitch))
            
            mean_pitch = float(np.mean(pitch_values)) if pitch_values else 0.0
            pitch_variance = float(np.var(pitch_values)) if pitch_values else 0.0
            pitch_range = float(max(pitch_values) - min(pitch_values)) if pitch_values else 0.0
            
            # Energy/intensity
            rms = librosa.feature.rms(y=audio_array)[0]
            mean_energy = float(np.mean(rms))
            energy_variance = float(np.var(rms))
            
            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_array, sr=sample_rate)[0]
            spectral_centroid_mean = float(np.mean(spectral_centroid))
            
            # Zero crossing rate (voice quality indicator)
            zcr = librosa.feature.zero_crossing_rate(audio_array)[0]
            zero_crossing_rate = float(np.mean(zcr))
            
            # Tempo and rhythm
            tempo, beats = librosa.beat.beat_track(y=audio_array, sr=sample_rate)
            tempo_value = float(tempo)
            
            # Speech rate estimation
            duration = float(len(audio_array) / sample_rate)
            
            # Pause detection (silence detection)
            silence_threshold = 0.01
            silent_frames = rms < silence_threshold
            pause_segments = self._find_pause_segments(silent_frames)
            pause_count = len(pause_segments)
            pause_frequency = float(pause_count / (duration / 60)) if duration > 0 else 0.0
            
            return AudioFeatures(
                mean_pitch=mean_pitch,
                pitch_variance=pitch_variance,
                pitch_range=pitch_range,
                mean_energy=mean_energy,
                energy_variance=energy_variance,
                spectral_centroid=spectral_centroid_mean,
                zero_crossing_rate=zero_crossing_rate,
                tempo=tempo_value,
                duration=duration,
                pause_count=pause_count,
                pause_frequency=pause_frequency
            )
            
        except Exception as e:
            logger.error(f"Audio feature analysis error: {e}")
            return AudioFeatures()
    
    def _find_pause_segments(self, silent_frames: np.ndarray, min_pause_length: int = 5) -> List[Tuple[int, int]]:
        """Find pause segments in audio"""
        pauses: List[Tuple[int, int]] = []
        in_pause = False
        pause_start = 0
        
        for i, is_silent in enumerate(silent_frames):
            if is_silent and not in_pause:
                in_pause = True
                pause_start = i
            elif not is_silent and in_pause:
                in_pause = False
                if i - pause_start >= min_pause_length:
                    pauses.append((pause_start, i))
        
        return pauses
    
    def classify_tone_emotion(self, features: AudioFeatures, transcription: str) -> Tuple[str, str, str]:
        """Classify tone and emotion based on audio features and transcription"""
        try:
            # Rule-based classification using audio features
            tone = "neutral"
            emotion = "neutral"
            sentiment = "neutral"
            
            # Tone classification based on pitch and energy
            if features.mean_pitch > 200:  # High pitch
                if features.pitch_variance > 1000:  # High variance
                    tone = "anxious"
                else:
                    tone = "calm"
            elif features.mean_pitch < 150:  # Low pitch
                if features.mean_energy < 0.02:  # Low energy
                    tone = "depressed"
                else:
                    tone = "calm"
            
            # Agitated detection
            if (features.energy_variance > 0.01 and 
                features.pause_frequency > 10):
                tone = "agitated"
            
            # Emotion classification
            if features.mean_energy > 0.05:  # High energy
                emotion = "excited"
            elif features.mean_energy < 0.01:  # Low energy
                emotion = "sad"
            elif features.pitch_variance > 1500:  # High pitch variance
                emotion = "anxious"
            
            # Use OpenAI for sentiment analysis if available
            if self.openai_client and transcription:
                sentiment = self._analyze_sentiment_with_ai(transcription)
            
            return tone, emotion, sentiment
            
        except Exception as e:
            logger.error(f"Tone/emotion classification error: {e}")
            return "neutral", "neutral", "neutral"
    
    def _analyze_sentiment_with_ai(self, transcription: str) -> str:
        """Analyze sentiment using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a clinical psychologist analyzing patient speech for sentiment. Respond with only 'positive', 'negative', or 'neutral'."},
                    {"role": "user", "content": f"Analyze the sentiment of this patient speech: '{transcription}'"}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            if sentiment not in ['positive', 'negative', 'neutral']:
                sentiment = 'neutral'
            
            return sentiment
            
        except Exception as e:
            logger.error(f"AI sentiment analysis error: {e}")
            return "neutral"
    
    def calculate_speech_rate(self, transcription: str, duration: float) -> float:
        """Calculate speech rate in words per minute"""
        if duration <= 0:
            return 0.0
        
        word_count = len(transcription.split())
        speech_rate = (word_count / duration) * 60  # words per minute
        return speech_rate
    
    async def analyze_voice_comprehensive(self, audio_data: str) -> VoiceAnalysis:
        """Comprehensive voice analysis including transcription, tone, and emotion"""
        try:
            # Transcribe audio
            transcription = await self.transcribe_audio(audio_data)
            
            # Analyze audio features
            features = self.analyze_audio_features(audio_data)
            
            # Classify tone and emotion
            tone, emotion, sentiment = self.classify_tone_emotion(features, transcription)
            
            # Calculate speech metrics
            duration = features.get('duration', 0)
            speech_rate = self.calculate_speech_rate(transcription, duration)
            pause_frequency = features.get('pause_frequency', 0)
            
            # Calculate confidence based on feature reliability
            confidence = self._calculate_confidence(features, transcription)
            
            return VoiceAnalysis(
                transcription=transcription,
                sentiment=sentiment,
                emotion=emotion,
                tone=tone,
                speech_rate=speech_rate,
                pause_frequency=pause_frequency,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Comprehensive voice analysis error: {e}")
            raise HTTPException(status_code=500, detail="Voice analysis failed")
    
    def _calculate_confidence(self, features: AudioFeatures, transcription: str) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on audio quality indicators
        if features.mean_energy > 0.01:
            confidence += 0.2
        
        if features.duration > 3:  # At least 3 seconds
            confidence += 0.2
        
        if len(transcription.split()) > 5:  # At least 5 words
            confidence += 0.1
        
        return min(confidence, 1.0)

# Global instance
audio_analysis_service = AudioAnalysisService()