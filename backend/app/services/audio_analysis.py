"""
Audio analysis service for voice tone and emotion detection
"""

import io
import base64
import json
import logging
from typing import Dict, Any, Optional, Tuple
import speech_recognition as sr
import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram
import librosa
import openai
from pydantic import BaseModel
from fastapi import HTTPException
from ..core.config import settings

logger = logging.getLogger(__name__)

class VoiceAnalysis(BaseModel):
    transcription: str
    sentiment: str = "neutral"  # positive, negative, neutral
    emotion: str = "neutral"
    tone: str = "neutral"  # calm, anxious, depressed, agitated, neutral
    speech_rate: float = 0.0  # words per minute
    pause_frequency: float = 0.0  # pauses per minute
    confidence: float = 0.0

class AudioAnalysisService:
    """Service for analyzing audio files for transcription and emotional content"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
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
    
    def analyze_audio_features(self, audio_data: str) -> Dict[str, Any]:
        """Analyze audio features for tone and emotion detection"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Load audio with librosa
            audio_array, sample_rate = librosa.load(io.BytesIO(audio_bytes), sr=None)
            
            # Extract features
            features = {}
            
            # Fundamental frequency (pitch)
            pitches, magnitudes = librosa.piptrack(y=audio_array, sr=sample_rate)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                features['mean_pitch'] = np.mean(pitch_values)
                features['pitch_variance'] = np.var(pitch_values)
                features['pitch_range'] = max(pitch_values) - min(pitch_values)
            else:
                features['mean_pitch'] = 0
                features['pitch_variance'] = 0
                features['pitch_range'] = 0
            
            # Energy/intensity
            rms = librosa.feature.rms(y=audio_array)[0]
            features['mean_energy'] = np.mean(rms)
            features['energy_variance'] = np.var(rms)
            
            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_array, sr=sample_rate)[0]
            features['spectral_centroid'] = np.mean(spectral_centroid)
            
            # Zero crossing rate (voice quality indicator)
            zcr = librosa.feature.zero_crossing_rate(audio_array)[0]
            features['zero_crossing_rate'] = np.mean(zcr)
            
            # Tempo and rhythm
            tempo, beats = librosa.beat.beat_track(y=audio_array, sr=sample_rate)
            features['tempo'] = tempo
            
            # Speech rate estimation
            duration = len(audio_array) / sample_rate
            features['duration'] = duration
            
            # Pause detection (silence detection)
            silence_threshold = 0.01
            silent_frames = rms < silence_threshold
            pause_segments = self._find_pause_segments(silent_frames)
            features['pause_count'] = len(pause_segments)
            features['pause_frequency'] = len(pause_segments) / (duration / 60)  # per minute
            
            return features
            
        except Exception as e:
            logger.error(f"Audio feature analysis error: {e}")
            return {}
    
    def _find_pause_segments(self, silent_frames: np.ndarray, min_pause_length: int = 5) -> list:
        """Find pause segments in audio"""
        pauses = []
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
    
    def classify_tone_emotion(self, features: Dict[str, Any], transcription: str) -> Tuple[str, str, str]:
        """Classify tone and emotion based on audio features and transcription"""
        try:
            # Rule-based classification using audio features
            tone = "neutral"
            emotion = "neutral"
            sentiment = "neutral"
            
            # Tone classification based on pitch and energy
            if features.get('mean_pitch', 0) > 200:  # High pitch
                if features.get('pitch_variance', 0) > 1000:  # High variance
                    tone = "anxious"
                else:
                    tone = "calm"
            elif features.get('mean_pitch', 0) < 150:  # Low pitch
                if features.get('mean_energy', 0) < 0.02:  # Low energy
                    tone = "depressed"
                else:
                    tone = "calm"
            
            # Agitated detection
            if (features.get('energy_variance', 0) > 0.01 and 
                features.get('pause_frequency', 0) > 10):
                tone = "agitated"
            
            # Emotion classification
            if features.get('mean_energy', 0) > 0.05:  # High energy
                emotion = "excited"
            elif features.get('mean_energy', 0) < 0.01:  # Low energy
                emotion = "sad"
            elif features.get('pitch_variance', 0) > 1500:  # High pitch variance
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
    
    def _calculate_confidence(self, features: Dict[str, Any], transcription: str) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on audio quality indicators
        if features.get('mean_energy', 0) > 0.01:
            confidence += 0.2
        
        if features.get('duration', 0) > 3:  # At least 3 seconds
            confidence += 0.2
        
        if len(transcription.split()) > 5:  # At least 5 words
            confidence += 0.1
        
        return min(confidence, 1.0)

# Global instance
audio_analysis_service = AudioAnalysisService()