"""
Voice analysis API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import logging

from ...core.database import get_async_db
from ...core.auth import get_current_user
from ...services.audio_analysis import audio_analysis_service, VoiceAnalysis
from ...models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])
security = HTTPBearer()

class TranscriptionRequest(BaseModel):
    audio_data: str  # base64 encoded audio

class TranscriptionResponse(BaseModel):
    transcription: str

class VoiceAnalysisRequest(BaseModel):
    audio_data: str  # base64 encoded audio

class VoiceAnalysisResponse(BaseModel):
    transcription: str
    sentiment: str
    emotion: str
    tone: str
    speech_rate: float
    pause_frequency: float
    confidence: float

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: TranscriptionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio to text using speech recognition
    """
    try:
        logger.info(f"Transcribing audio for user: {current_user.email}")
        
        # Validate user is licensed
        if not current_user.is_licensed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voice analysis requires licensed practitioner"
            )
        
        # Transcribe audio
        transcription = await audio_analysis_service.transcribe_audio(request.audio_data)
        
        logger.info(f"Audio transcription completed for user: {current_user.email}")
        
        return TranscriptionResponse(transcription=transcription)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audio transcription failed"
        )

@router.post("/analyze", response_model=VoiceAnalysisResponse)
async def analyze_voice(
    request: VoiceAnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive voice analysis including transcription, tone, and emotion detection
    """
    try:
        logger.info(f"Analyzing voice for user: {current_user.email}")
        
        # Validate user is licensed
        if not current_user.is_licensed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voice analysis requires licensed practitioner"
            )
        
        # Perform comprehensive voice analysis
        analysis = await audio_analysis_service.analyze_voice_comprehensive(request.audio_data)
        
        logger.info(f"Voice analysis completed for user: {current_user.email}")
        
        return VoiceAnalysisResponse(
            transcription=analysis.transcription,
            sentiment=analysis.sentiment,
            emotion=analysis.emotion,
            tone=analysis.tone,
            speech_rate=analysis.speech_rate,
            pause_frequency=analysis.pause_frequency,
            confidence=analysis.confidence
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice analysis error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice analysis failed"
        )

@router.get("/health")
async def voice_health_check():
    """
    Health check for voice analysis service
    """
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