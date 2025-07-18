"""
Custom exceptions for therapy-assistant-agent application.
Provides structured error handling with proper HTTP status codes.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseAppException(Exception):
    """Base exception class for application-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(BaseAppException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AUTH_FAILED",
            details=details,
        )


class AuthorizationError(BaseAppException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PERMISSIONS",
            details=details,
        )


class ValidationError(BaseAppException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if field:
            details = details or {}
            details["field"] = field
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class DatabaseError(BaseAppException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if operation:
            details = details or {}
            details["operation"] = operation
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
        )


class OpenAIServiceError(BaseAppException):
    """Raised when OpenAI API operations fail."""

    def __init__(
        self,
        message: str = "AI service error",
        api_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if api_error:
            details = details or {}
            details["api_error"] = api_error
        super().__init__(
            message=message,
            error_code="OPENAI_ERROR",
            details=details,
        )


class RateLimitError(BaseAppException):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if retry_after:
            details = details or {}
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMITED",
            details=details,
        )


class AudioProcessingError(BaseAppException):
    """Raised when audio processing fails."""

    def __init__(
        self,
        message: str = "Audio processing failed",
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if stage:
            details = details or {}
            details["processing_stage"] = stage
        super().__init__(
            message=message,
            error_code="AUDIO_PROCESSING_ERROR",
            details=details,
        )


class FileOperationError(BaseAppException):
    """Raised when file operations fail."""

    def __init__(
        self,
        message: str = "File operation failed",
        operation: Optional[str] = None,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details = details or {}
        if operation:
            details["operation"] = operation
        if file_path:
            details["file_path"] = file_path
        super().__init__(
            message=message,
            error_code="FILE_OPERATION_ERROR",
            details=details,
        )


class SecurityError(BaseAppException):
    """Raised when security violations are detected."""

    def __init__(
        self,
        message: str = "Security violation detected",
        violation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if violation_type:
            details = details or {}
            details["violation_type"] = violation_type
        super().__init__(
            message=message,
            error_code="SECURITY_VIOLATION",
            details=details,
        )


# HTTP Exception mapping
def map_to_http_exception(error: BaseAppException) -> HTTPException:
    """Map application exceptions to HTTP exceptions with appropriate status codes."""
    
    status_code_mapping = {
        "AUTH_FAILED": status.HTTP_401_UNAUTHORIZED,
        "INSUFFICIENT_PERMISSIONS": status.HTTP_403_FORBIDDEN,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "OPENAI_ERROR": status.HTTP_502_BAD_GATEWAY,
        "RATE_LIMITED": status.HTTP_429_TOO_MANY_REQUESTS,
        "AUDIO_PROCESSING_ERROR": status.HTTP_400_BAD_REQUEST,
        "FILE_OPERATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "SECURITY_VIOLATION": status.HTTP_400_BAD_REQUEST,
    }
    
    status_code = status_code_mapping.get(
        error.error_code, 
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    detail = {
        "error": error.error_code,
        "message": error.message,
        "details": error.details,
    }
    
    # Add retry-after header for rate limiting
    headers = {}
    if error.error_code == "RATE_LIMITED" and "retry_after" in error.details:
        headers["Retry-After"] = str(error.details["retry_after"])
    
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers if headers else None,
    )


# Context managers for error handling
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def handle_database_errors(
    operation: str,
) -> AsyncGenerator[None, None]:
    """Context manager for handling database errors."""
    try:
        yield
    except Exception as e:
        logger.error(f"Database error during {operation}: {e}")
        raise DatabaseError(
            message=f"Database operation '{operation}' failed",
            operation=operation,
            details={"original_error": str(e)},
        ) from e


@asynccontextmanager
async def handle_openai_errors() -> AsyncGenerator[None, None]:
    """Context manager for handling OpenAI API errors."""
    try:
        yield
    except Exception as e:
        error_msg = str(e).lower()
        
        if "rate_limit" in error_msg:
            raise RateLimitError(
                message="AI service rate limit exceeded",
                retry_after=60,
                details={"original_error": str(e)},
            ) from e
        elif "invalid_request" in error_msg:
            raise OpenAIServiceError(
                message="Invalid request to AI service",
                api_error="invalid_request",
                details={"original_error": str(e)},
            ) from e
        else:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIServiceError(
                message="AI service temporarily unavailable",
                api_error="unknown",
                details={"original_error": str(e)},
            ) from e


@asynccontextmanager
async def handle_audio_processing_errors(
    stage: str,
) -> AsyncGenerator[None, None]:
    """Context manager for handling audio processing errors."""
    try:
        yield
    except Exception as e:
        logger.error(f"Audio processing error at {stage}: {e}")
        raise AudioProcessingError(
            message=f"Audio processing failed at {stage}",
            stage=stage,
            details={"original_error": str(e)},
        ) from e


# Utility functions
def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "error": error_code,
        "message": message,
        "details": details or {},
        "success": False,
    }


def is_client_error(error: BaseAppException) -> bool:
    """Check if error is a client error (4xx) vs server error (5xx)."""
    client_error_codes = {
        "AUTH_FAILED",
        "INSUFFICIENT_PERMISSIONS", 
        "VALIDATION_ERROR",
        "RATE_LIMITED",
        "AUDIO_PROCESSING_ERROR",
        "SECURITY_VIOLATION",
    }
    return error.error_code in client_error_codes