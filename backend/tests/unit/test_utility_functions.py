# Unit tests for utility functions

import pytest
from unittest.mock import Mock, patch, mock_open, AsyncMock
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import asyncio

from app.main_auth_async import hash_password, verify_password, create_access_token, decode_token
from app.core.config import Settings, get_settings


@pytest.mark.unit
@pytest.mark.utilities
class TestPasswordUtilities:
    """Test cases for password utility functions."""
    
    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a hash."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_different_for_same_input(self):
        """Test that hash_password creates different hashes for same input."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Should be different due to salt
        assert hash1 != hash2
    
    def test_verify_password_correct_password(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_password(self):
        """Test password verification with empty password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False
    
    def test_verify_password_none_password(self):
        """Test password verification with None password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(None, hashed) is False
    
    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "testpassword123"
        invalid_hash = "invalid_hash"
        
        assert verify_password(password, invalid_hash) is False


@pytest.mark.unit
@pytest.mark.utilities
class TestJWTUtilities:
    """Test cases for JWT utility functions."""
    
    def test_create_access_token_basic(self):
        """Test basic JWT token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT has dots
    
    def test_create_access_token_with_expiration(self):
        """Test JWT token creation with custom expiration."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify expiration is set correctly
        payload = decode_token(token)
        assert payload is not None
        assert "exp" in payload
    
    def test_create_access_token_with_additional_claims(self):
        """Test JWT token creation with additional claims."""
        data = {
            "sub": "test@example.com",
            "role": "therapist",
            "license": "LMFT"
        }
        token = create_access_token(data)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "therapist"
        assert payload["license"] == "LMFT"
    
    def test_decode_token_valid_token(self):
        """Test JWT token decoding with valid token."""
        data = {"sub": "test@example.com", "role": "therapist"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "therapist"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_token_invalid_token(self):
        """Test JWT token decoding with invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = decode_token(invalid_token)
        assert payload is None
    
    def test_decode_token_malformed_token(self):
        """Test JWT token decoding with malformed token."""
        malformed_token = "notajwt"
        
        payload = decode_token(malformed_token)
        assert payload is None
    
    def test_decode_token_expired_token(self):
        """Test JWT token decoding with expired token."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta)
        
        payload = decode_token(token)
        assert payload is None
    
    def test_decode_token_none_token(self):
        """Test JWT token decoding with None token."""
        payload = decode_token(None)
        assert payload is None
    
    def test_decode_token_empty_token(self):
        """Test JWT token decoding with empty token."""
        payload = decode_token("")
        assert payload is None


@pytest.mark.unit
@pytest.mark.utilities
class TestSettings:
    """Test cases for settings configuration."""
    
    def test_settings_creation(self):
        """Test basic settings creation."""
        settings = Settings()
        
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'ALGORITHM')
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
    
    def test_settings_defaults(self):
        """Test settings default values."""
        settings = Settings()
        
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.DEBUG is False
    
    @patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost/test',
        'SECRET_KEY': 'test-secret-key',
        'OPENAI_API_KEY': 'test-openai-key',
        'DEBUG': 'true'
    })
    def test_settings_from_environment(self):
        """Test settings loaded from environment variables."""
        settings = Settings()
        
        assert settings.DATABASE_URL == 'postgresql://test:test@localhost/test'
        assert settings.SECRET_KEY == 'test-secret-key'
        assert settings.OPENAI_API_KEY == 'test-openai-key'
        assert settings.DEBUG is True
    
    @patch.dict(os.environ, {
        'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'
    })
    def test_settings_cors_origins_parsing(self):
        """Test CORS origins parsing."""
        settings = Settings()
        
        expected_origins = ['http://localhost:3000', 'http://localhost:8080']
        assert settings.CORS_ORIGINS == expected_origins
    
    @patch.dict(os.environ, {
        'ACCESS_TOKEN_EXPIRE_MINUTES': '60'
    })
    def test_settings_integer_parsing(self):
        """Test integer setting parsing."""
        settings = Settings()
        
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2


@pytest.mark.unit
@pytest.mark.utilities
class TestAsyncFileService:
    """Test cases for async file service utilities."""
    
    @pytest.mark.asyncio
    async def test_read_text_file_exists(self):
        """Test reading text file that exists."""
        from app.services.async_file_service import AsyncFileService
        
        test_content = "This is test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            content = await service.read_text(temp_path)
            assert content == test_content
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_read_text_file_not_exists(self):
        """Test reading text file that doesn't exist."""
        from app.services.async_file_service import AsyncFileService
        
        service = AsyncFileService()
        with pytest.raises(FileNotFoundError):
            await service.read_text("/nonexistent/file.txt")
    
    @pytest.mark.asyncio
    async def test_write_text_file(self):
        """Test writing text file."""
        from app.services.async_file_service import AsyncFileService
        
        test_content = "This is test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            await service.write_text(temp_path, test_content)
            
            # Verify content was written
            content = await service.read_text(temp_path)
            assert content == test_content
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_read_json_valid_file(self):
        """Test reading valid JSON file."""
        from app.services.async_file_service import AsyncFileService
        
        test_data = {"key": "value", "number": 42}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            data = await service.read_json(temp_path)
            assert data == test_data
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_read_json_invalid_file(self):
        """Test reading invalid JSON file."""
        from app.services.async_file_service import AsyncFileService
        
        invalid_json = "{ invalid json"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(invalid_json)
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            with pytest.raises(json.JSONDecodeError):
                await service.read_json(temp_path)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_write_json_file(self):
        """Test writing JSON file."""
        from app.services.async_file_service import AsyncFileService
        
        test_data = {"key": "value", "number": 42}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            await service.write_json(temp_path, test_data)
            
            # Verify content was written
            data = await service.read_json(temp_path)
            assert data == test_data
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_file_exists_true(self):
        """Test file_exists returns True for existing file."""
        from app.services.async_file_service import AsyncFileService
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            exists = await service.file_exists(temp_path)
            assert exists is True
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_file_exists_false(self):
        """Test file_exists returns False for non-existing file."""
        from app.services.async_file_service import AsyncFileService
        
        service = AsyncFileService()
        exists = await service.file_exists("/nonexistent/file.txt")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_get_file_size(self):
        """Test getting file size."""
        from app.services.async_file_service import AsyncFileService
        
        test_content = "This is test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            size = await service.get_file_size(temp_path)
            assert size == len(test_content)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test deleting file."""
        from app.services.async_file_service import AsyncFileService
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        service = AsyncFileService()
        assert await service.file_exists(temp_path) is True
        
        await service.delete_file(temp_path)
        assert await service.file_exists(temp_path) is False
    
    @pytest.mark.asyncio
    async def test_read_lines(self):
        """Test reading file lines."""
        from app.services.async_file_service import AsyncFileService
        
        test_lines = ["Line 1", "Line 2", "Line 3"]
        test_content = "\n".join(test_lines)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            lines = await service.read_lines(temp_path)
            assert lines == test_lines
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_write_lines(self):
        """Test writing file lines."""
        from app.services.async_file_service import AsyncFileService
        
        test_lines = ["Line 1", "Line 2", "Line 3"]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            await service.write_lines(temp_path, test_lines)
            
            # Verify lines were written
            lines = await service.read_lines(temp_path)
            assert lines == test_lines
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_append_text(self):
        """Test appending text to file."""
        from app.services.async_file_service import AsyncFileService
        
        initial_content = "Initial content"
        append_content = " appended"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(initial_content)
            temp_path = f.name
        
        try:
            service = AsyncFileService()
            await service.append_text(temp_path, append_content)
            
            # Verify content was appended
            content = await service.read_text(temp_path)
            assert content == initial_content + append_content
        finally:
            os.unlink(temp_path)


@pytest.mark.unit
@pytest.mark.utilities
class TestDataLoader:
    """Test cases for data loader utilities."""
    
    @pytest.mark.asyncio
    async def test_load_synthetic_cases_success(self):
        """Test loading synthetic cases successfully."""
        from app.services.async_file_service import load_synthetic_cases
        
        mock_cases = [
            {"id": "case1", "disorder": "Depression", "symptoms": ["sadness", "fatigue"]},
            {"id": "case2", "disorder": "Anxiety", "symptoms": ["worry", "restlessness"]}
        ]
        
        with patch('app.services.async_file_service.AsyncFileService.read_json') as mock_read:
            mock_read.return_value = mock_cases
            
            cases = await load_synthetic_cases()
            assert cases == mock_cases
            mock_read.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_synthetic_cases_file_not_found(self):
        """Test loading synthetic cases when file not found."""
        from app.services.async_file_service import load_synthetic_cases
        
        with patch('app.services.async_file_service.AsyncFileService.read_json') as mock_read:
            mock_read.side_effect = FileNotFoundError("File not found")
            
            cases = await load_synthetic_cases()
            assert cases == []
    
    @pytest.mark.asyncio
    async def test_load_synthetic_cases_invalid_json(self):
        """Test loading synthetic cases with invalid JSON."""
        from app.services.async_file_service import load_synthetic_cases
        
        with patch('app.services.async_file_service.AsyncFileService.read_json') as mock_read:
            mock_read.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            
            cases = await load_synthetic_cases()
            assert cases == []
    
    @pytest.mark.asyncio
    async def test_save_analysis_result(self):
        """Test saving analysis result."""
        from app.services.async_file_service import save_analysis_result
        
        result_data = {"analysis": "test", "timestamp": "2023-01-01T00:00:00Z"}
        
        with patch('app.services.async_file_service.AsyncFileService.write_json') as mock_write:
            await save_analysis_result("test_analysis", result_data)
            mock_write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_user_activity(self):
        """Test logging user activity."""
        from app.services.async_file_service import log_user_activity
        
        activity_data = {
            "user_id": "user123",
            "action": "login",
            "timestamp": "2023-01-01T00:00:00Z"
        }
        
        with patch('app.services.async_file_service.AsyncFileService.append_text') as mock_append:
            await log_user_activity("user123", "login", {"ip": "127.0.0.1"})
            mock_append.assert_called_once()


@pytest.mark.unit
@pytest.mark.utilities
class TestAsyncHttpService:
    """Test cases for async HTTP service utilities."""
    
    @pytest.mark.asyncio
    async def test_http_service_get_request(self):
        """Test HTTP GET request."""
        from app.services.async_http_service import AsyncHttpService
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch('httpx.AsyncClient.get', return_value=mock_response) as mock_get:
            service = AsyncHttpService()
            response = await service.get("https://example.com/api/data")
            
            assert response.status_code == 200
            assert response.json() == {"data": "test"}
            mock_get.assert_called_once_with("https://example.com/api/data")
    
    @pytest.mark.asyncio
    async def test_http_service_post_request(self):
        """Test HTTP POST request."""
        from app.services.async_http_service import AsyncHttpService
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123"}
        
        post_data = {"name": "test"}
        
        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            service = AsyncHttpService()
            response = await service.post("https://example.com/api/data", json=post_data)
            
            assert response.status_code == 201
            assert response.json() == {"id": "123"}
            mock_post.assert_called_once_with("https://example.com/api/data", json=post_data)
    
    @pytest.mark.asyncio
    async def test_http_service_client_lifecycle(self):
        """Test HTTP service client lifecycle."""
        from app.services.async_http_service import AsyncHttpService
        
        service = AsyncHttpService()
        
        # Client should be created on first use
        assert service._client is None
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = service.get_client()
            assert client is mock_client
            assert service._client is mock_client
            
            # Should reuse existing client
            client2 = service.get_client()
            assert client2 is mock_client
    
    @pytest.mark.asyncio
    async def test_http_service_close(self):
        """Test HTTP service close."""
        from app.services.async_http_service import AsyncHttpService
        
        service = AsyncHttpService()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            service.get_client()
            assert service._client is mock_client
            
            await service.close()
            mock_client.aclose.assert_called_once()
            assert service._client is None
    
    @pytest.mark.asyncio
    async def test_fetch_external_data(self):
        """Test fetch external data helper."""
        from app.services.async_http_service import fetch_external_data
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"external": "data"}
        
        with patch('app.services.async_http_service.AsyncHttpService.get', return_value=mock_response):
            data = await fetch_external_data("https://api.example.com/data")
            assert data == {"external": "data"}
    
    @pytest.mark.asyncio
    async def test_post_external_data(self):
        """Test post external data helper."""
        from app.services.async_http_service import post_external_data
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"created": True}
        
        post_data = {"data": "test"}
        
        with patch('app.services.async_http_service.AsyncHttpService.post', return_value=mock_response):
            response = await post_external_data("https://api.example.com/data", post_data)
            assert response == {"created": True}


@pytest.mark.unit
@pytest.mark.utilities
class TestSecurityUtilities:
    """Test cases for security utility functions."""
    
    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        from app.utils.security import sanitize_input
        
        # Test with safe input
        safe_input = "This is safe text"
        result = sanitize_input(safe_input)
        assert result == safe_input
        
        # Test with potentially dangerous input
        dangerous_input = "<script>alert('xss')</script>"
        result = sanitize_input(dangerous_input)
        assert "<script>" not in result
        assert "alert" not in result
    
    def test_sanitize_input_sql_injection(self):
        """Test input sanitization against SQL injection."""
        from app.utils.security import sanitize_input
        
        sql_injection = "'; DROP TABLE users; --"
        result = sanitize_input(sql_injection)
        assert "DROP TABLE" not in result
        assert "--" not in result
    
    def test_sanitize_input_dict(self):
        """Test input sanitization with dictionary."""
        from app.utils.security import sanitize_input
        
        input_dict = {
            "name": "John",
            "comment": "<script>alert('xss')</script>",
            "age": 30
        }
        
        result = sanitize_input(input_dict)
        assert result["name"] == "John"
        assert result["age"] == 30
        assert "<script>" not in result["comment"]
    
    def test_sanitize_input_list(self):
        """Test input sanitization with list."""
        from app.utils.security import sanitize_input
        
        input_list = ["safe text", "<script>alert('xss')</script>", "another safe text"]
        
        result = sanitize_input(input_list)
        assert result[0] == "safe text"
        assert result[2] == "another safe text"
        assert "<script>" not in result[1]
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from app.utils.security import SecurityManager
        
        manager = SecurityManager()
        
        # Test safe filename
        safe_filename = "document.pdf"
        result = manager.sanitize_filename(safe_filename)
        assert result == safe_filename
        
        # Test dangerous filename
        dangerous_filename = "../../../etc/passwd"
        result = manager.sanitize_filename(dangerous_filename)
        assert "../" not in result
        assert "passwd" in result  # Should keep the actual filename part
    
    def test_validate_ip_address(self):
        """Test IP address validation."""
        from app.utils.security import SecurityManager
        
        manager = SecurityManager()
        
        # Valid IPv4
        assert manager.validate_ip_address("192.168.1.1") is True
        assert manager.validate_ip_address("127.0.0.1") is True
        
        # Valid IPv6
        assert manager.validate_ip_address("::1") is True
        assert manager.validate_ip_address("2001:db8::1") is True
        
        # Invalid IPs
        assert manager.validate_ip_address("999.999.999.999") is False
        assert manager.validate_ip_address("not.an.ip") is False
        assert manager.validate_ip_address("") is False
    
    def test_is_suspicious_request(self):
        """Test suspicious request detection."""
        from app.utils.security import SecurityManager
        
        manager = SecurityManager()
        
        # Safe request
        safe_request = "SELECT * FROM users WHERE id = 1"
        assert manager.is_suspicious_request(safe_request) is False
        
        # SQL injection attempt
        sql_injection = "SELECT * FROM users WHERE id = 1'; DROP TABLE users; --"
        assert manager.is_suspicious_request(sql_injection) is True
        
        # XSS attempt
        xss_attempt = "<script>alert('xss')</script>"
        assert manager.is_suspicious_request(xss_attempt) is True
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        from app.utils.security import SecurityManager
        
        manager = SecurityManager()
        
        # Test default length
        token = manager.generate_secure_token()
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Test custom length
        token32 = manager.generate_secure_token(length=32)
        assert len(token32) == 64  # 32 bytes = 64 hex chars
        
        # Test tokens are different
        token1 = manager.generate_secure_token()
        token2 = manager.generate_secure_token()
        assert token1 != token2
    
    def test_hash_and_verify_sensitive_data(self):
        """Test hashing and verifying sensitive data."""
        from app.utils.security import SecurityManager
        
        manager = SecurityManager()
        
        sensitive_data = "sensitive_information_123"
        
        # Hash the data
        hashed = manager.hash_sensitive_data(sensitive_data)
        assert hashed != sensitive_data
        assert isinstance(hashed, str)
        
        # Verify correct data
        assert manager.verify_hashed_data(sensitive_data, hashed) is True
        
        # Verify incorrect data
        assert manager.verify_hashed_data("wrong_data", hashed) is False


@pytest.mark.unit
@pytest.mark.utilities
class TestValidationUtilities:
    """Test cases for validation utility functions."""
    
    def test_validate_clinical_content_safe(self):
        """Test clinical content validation with safe content."""
        from app.utils.validators import validate_clinical_content
        
        safe_content = "Patient reports feeling depressed with low energy."
        result = validate_clinical_content(safe_content)
        assert result is True
    
    def test_validate_clinical_content_inappropriate(self):
        """Test clinical content validation with inappropriate content."""
        from app.utils.validators import validate_clinical_content
        
        inappropriate_content = "Patient is being violent and dangerous."
        result = validate_clinical_content(inappropriate_content)
        # Should flag potentially harmful content
        assert result is False
    
    def test_validate_datetime_range_valid(self):
        """Test datetime range validation with valid range."""
        from app.utils.validators import validate_datetime_range
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=1)
        
        result = validate_datetime_range(start_date, end_date)
        assert result is True
    
    def test_validate_datetime_range_invalid(self):
        """Test datetime range validation with invalid range."""
        from app.utils.validators import validate_datetime_range
        
        start_date = datetime.now()
        end_date = start_date - timedelta(days=1)  # End before start
        
        result = validate_datetime_range(start_date, end_date)
        assert result is False
    
    def test_validate_file_upload_valid(self):
        """Test file upload validation with valid file."""
        from app.utils.validators import validate_file_upload
        
        valid_file = {
            "filename": "document.pdf",
            "size": 1024000,  # 1MB
            "content_type": "application/pdf"
        }
        
        result = validate_file_upload(valid_file)
        assert result is True
    
    def test_validate_file_upload_too_large(self):
        """Test file upload validation with file too large."""
        from app.utils.validators import validate_file_upload
        
        large_file = {
            "filename": "large_document.pdf",
            "size": 100000000,  # 100MB
            "content_type": "application/pdf"
        }
        
        result = validate_file_upload(large_file)
        assert result is False
    
    def test_validate_file_upload_invalid_type(self):
        """Test file upload validation with invalid file type."""
        from app.utils.validators import validate_file_upload
        
        invalid_file = {
            "filename": "script.exe",
            "size": 1024,
            "content_type": "application/x-msdownload"
        }
        
        result = validate_file_upload(invalid_file)
        assert result is False


@pytest.mark.unit
@pytest.mark.utilities
class TestRateLimiter:
    """Test cases for rate limiter utility."""
    
    def test_rate_limiter_allows_within_limit(self):
        """Test rate limiter allows requests within limit."""
        from app.utils.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        # Should allow requests within limit
        for i in range(5):
            assert limiter.is_allowed("user123") is True
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test rate limiter blocks requests over limit."""
        from app.utils.security import RateLimiter
        
        limiter = RateLimiter(max_requests=3, time_window=60)
        
        # Allow first 3 requests
        for i in range(3):
            assert limiter.is_allowed("user123") is True
        
        # Block 4th request
        assert limiter.is_allowed("user123") is False
    
    def test_rate_limiter_different_users(self):
        """Test rate limiter handles different users separately."""
        from app.utils.security import RateLimiter
        
        limiter = RateLimiter(max_requests=2, time_window=60)
        
        # Each user should have their own limit
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user2") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user2") is True
        
        # Third request should be blocked for each user
        assert limiter.is_allowed("user1") is False
        assert limiter.is_allowed("user2") is False
    
    def test_rate_limiter_cleanup(self):
        """Test rate limiter cleanup of old entries."""
        from app.utils.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, time_window=1)  # 1 second window
        
        # Make requests
        for i in range(3):
            limiter.is_allowed("user123")
        
        # Should have entries
        assert len(limiter.requests.get("user123", [])) == 3
        
        # Wait for cleanup (in real implementation)
        import time
        time.sleep(1.1)
        
        # Cleanup should remove old entries
        limiter._cleanup_old_entries("user123")
        assert len(limiter.requests.get("user123", [])) == 0