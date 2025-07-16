# Unit tests for web routes

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from urllib.parse import quote


@pytest.mark.unit
@pytest.mark.web
class TestWebRoutes:
    """Test cases for web interface routes."""
    
    def test_home_redirect_to_login_no_user(self, web_client):
        """Test home page redirects to login when no user."""
        response = web_client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    def test_home_redirect_to_dashboard_with_user(self, web_client, test_user):
        """Test home page redirects to dashboard when user is logged in."""
        # Mock the cookie-based authentication
        with patch('app.main_web.get_current_user_from_cookie', return_value=test_user.email):
            response = web_client.get("/", follow_redirects=False)
            assert response.status_code == 302
            assert response.headers["location"] == "/dashboard"
    
    def test_login_page_get(self, web_client):
        """Test login page GET request."""
        response = web_client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_login_post_success(self, web_client, test_user):
        """Test successful login POST."""
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }
        
        response = web_client.post("/login", data=login_data, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"
        
        # Check that cookie is set
        assert "token" in response.cookies
    
    @pytest.mark.asyncio
    async def test_login_post_invalid_credentials(self, web_client, test_user):
        """Test login POST with invalid credentials."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = web_client.post("/login", data=login_data)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Should show login form with error
    
    @pytest.mark.asyncio
    async def test_login_post_nonexistent_user(self, web_client):
        """Test login POST with nonexistent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = web_client.post("/login", data=login_data)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_login_post_inactive_user(self, web_client, async_db):
        """Test login POST with inactive user."""
        from app.main_auth_async import User, UserRole, hash_password
        
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
        
        response = web_client.post("/login", data=login_data)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_login_post_exception_handling(self, web_client):
        """Test login POST with exception handling."""
        with patch('app.main_web.select', side_effect=Exception("Database error")):
            login_data = {
                "username": "test@example.com",
                "password": "password123"
            }
            
            response = web_client.post("/login", data=login_data)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    def test_logout(self, web_client):
        """Test logout endpoint."""
        response = web_client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
        
        # Check that token cookie is deleted
        assert "token" in response.cookies
        assert response.cookies["token"] == ""
    
    @pytest.mark.asyncio
    async def test_dashboard_redirect_unauthorized(self, web_client):
        """Test dashboard redirects when unauthorized."""
        response = web_client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_dashboard_success(self, web_client, test_user):
        """Test dashboard page with authorized user."""
        # Mock the user authentication
        with patch('app.main_web.get_current_user_required', return_value=test_user):
            response = web_client.get("/dashboard")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_diagnostic_page_unauthorized(self, web_client):
        """Test diagnostic page redirects when unauthorized."""
        response = web_client.get("/diagnostic", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_diagnostic_page_success(self, web_client, test_user):
        """Test diagnostic page with authorized user."""
        with patch('app.main_web.get_current_user_required', return_value=test_user):
            response = web_client.get("/diagnostic")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_diagnostic_post_unauthorized(self, web_client):
        """Test diagnostic POST redirects when unauthorized."""
        diagnostic_data = {
            "symptoms": "test symptoms",
            "patient_context": "test context"
        }
        
        response = web_client.post("/diagnostic", data=diagnostic_data, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_diagnostic_post_no_openai(self, web_client, test_user):
        """Test diagnostic POST without OpenAI."""
        with patch('app.main_web.get_current_user_required', return_value=test_user), \
             patch('app.main_web.openai_client', None):
            
            diagnostic_data = {
                "symptoms": "test symptoms",
                "patient_context": "test context"
            }
            
            response = web_client.post("/diagnostic", data=diagnostic_data)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_diagnostic_post_with_openai(self, web_client, test_user, mock_async_openai_client):
        """Test diagnostic POST with OpenAI."""
        with patch('app.main_web.get_current_user_required', return_value=test_user), \
             patch('app.main_web.openai_client', mock_async_openai_client):
            
            diagnostic_data = {
                "symptoms": "Patient reports feeling sad and anxious",
                "patient_context": "29-year-old teacher"
            }
            
            response = web_client.post("/diagnostic", data=diagnostic_data)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_diagnostic_post_openai_error(self, web_client, test_user):
        """Test diagnostic POST with OpenAI error."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API error")
        
        with patch('app.main_web.get_current_user_required', return_value=test_user), \
             patch('app.main_web.openai_client', mock_client):
            
            diagnostic_data = {
                "symptoms": "test symptoms",
                "patient_context": "test context"
            }
            
            response = web_client.post("/diagnostic", data=diagnostic_data)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_treatment_page_unauthorized(self, web_client):
        """Test treatment page redirects when unauthorized."""
        response = web_client.get("/treatment", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_treatment_page_success(self, web_client, test_user):
        """Test treatment page with authorized user."""
        with patch('app.main_web.get_current_user_required', return_value=test_user):
            response = web_client.get("/treatment")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_treatment_post_unauthorized(self, web_client):
        """Test treatment POST redirects when unauthorized."""
        treatment_data = {
            "diagnosis": "Major Depressive Disorder",
            "patient_context": "test context"
        }
        
        response = web_client.post("/treatment", data=treatment_data, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_treatment_post_no_openai(self, web_client, test_user):
        """Test treatment POST without OpenAI."""
        with patch('app.main_web.get_current_user_required', return_value=test_user), \
             patch('app.main_web.openai_client', None):
            
            treatment_data = {
                "diagnosis": "Major Depressive Disorder",
                "patient_context": "test context"
            }
            
            response = web_client.post("/treatment", data=treatment_data)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_treatment_post_with_openai(self, web_client, test_user, mock_async_openai_client):
        """Test treatment POST with OpenAI."""
        with patch('app.main_web.get_current_user_required', return_value=test_user), \
             patch('app.main_web.openai_client', mock_async_openai_client):
            
            treatment_data = {
                "diagnosis": "Major Depressive Disorder",
                "patient_context": "Patient responds well to CBT"
            }
            
            response = web_client.post("/treatment", data=treatment_data)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_treatment_post_openai_error(self, web_client, test_user):
        """Test treatment POST with OpenAI error."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API error")
        
        with patch('app.main_web.get_current_user_required', return_value=test_user), \
             patch('app.main_web.openai_client', mock_client):
            
            treatment_data = {
                "diagnosis": "Major Depressive Disorder",
                "patient_context": "test context"
            }
            
            response = web_client.post("/treatment", data=treatment_data)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_cases_page_unauthorized(self, web_client):
        """Test cases page redirects when unauthorized."""
        response = web_client.get("/cases", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_cases_page_success(self, web_client, test_user):
        """Test cases page with authorized user."""
        with patch('app.main_web.get_current_user_required', return_value=test_user):
            response = web_client.get("/cases")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_cases_page_load_error(self, web_client, test_user):
        """Test cases page with loading error."""
        with patch('app.main_web.get_current_user_required', return_value=test_user), \
             patch('app.services.async_file_service.load_synthetic_cases', side_effect=Exception("Load error")):
            
            response = web_client.get("/cases")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    def test_health_check(self, web_client):
        """Test health check endpoint."""
        response = web_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "openai_available" in data
    
    def test_404_handler(self, web_client):
        """Test 404 error handler."""
        response = web_client.get("/nonexistent-page")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
    
    def test_500_handler(self, web_client):
        """Test 500 error handler."""
        # Mock an endpoint to raise an exception
        with patch('app.main_web.health_check', side_effect=Exception("Internal error")):
            response = web_client.get("/health")
            assert response.status_code == 500
            assert "text/html" in response.headers["content-type"]


@pytest.mark.unit
@pytest.mark.web
class TestWebUtilities:
    """Test cases for web utility functions."""
    
    def test_get_current_user_from_cookie_no_token(self):
        """Test get_current_user_from_cookie with no token."""
        from app.main_web import get_current_user_from_cookie
        
        result = get_current_user_from_cookie(None)
        assert result is None
    
    def test_get_current_user_from_cookie_invalid_token(self):
        """Test get_current_user_from_cookie with invalid token."""
        from app.main_web import get_current_user_from_cookie
        
        result = get_current_user_from_cookie("invalid_token")
        assert result is None
    
    def test_get_current_user_from_cookie_valid_token(self, test_user):
        """Test get_current_user_from_cookie with valid token."""
        from app.main_web import get_current_user_from_cookie
        from app.main_auth_async import create_access_token
        
        token = create_access_token(data={"sub": test_user.email})
        
        result = get_current_user_from_cookie(token)
        assert result == test_user.email
    
    def test_get_current_user_from_cookie_no_subject(self):
        """Test get_current_user_from_cookie with token missing subject."""
        from app.main_web import get_current_user_from_cookie
        from app.main_auth_async import create_access_token
        
        token = create_access_token(data={"other": "data"})
        
        result = get_current_user_from_cookie(token)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_required_no_token(self, web_client, async_db):
        """Test get_current_user_required with no token."""
        from app.main_web import get_current_user_required
        from fastapi import Request
        
        # Mock request with no token
        request = Mock(spec=Request)
        request.cookies = {}
        
        result = await get_current_user_required(request, async_db)
        
        # Should return redirect response
        assert hasattr(result, 'status_code')
        assert result.status_code == 302
    
    @pytest.mark.asyncio
    async def test_get_current_user_required_invalid_token(self, web_client, async_db):
        """Test get_current_user_required with invalid token."""
        from app.main_web import get_current_user_required
        from fastapi import Request
        
        # Mock request with invalid token
        request = Mock(spec=Request)
        request.cookies = {"token": "invalid_token"}
        
        result = await get_current_user_required(request, async_db)
        
        # Should return redirect response
        assert hasattr(result, 'status_code')
        assert result.status_code == 302
    
    @pytest.mark.asyncio
    async def test_get_current_user_required_valid_token(self, web_client, async_db, test_user):
        """Test get_current_user_required with valid token."""
        from app.main_web import get_current_user_required
        from app.main_auth_async import create_access_token
        from fastapi import Request
        
        token = create_access_token(data={"sub": test_user.email})
        
        # Mock request with valid token
        request = Mock(spec=Request)
        request.cookies = {"token": token}
        
        result = await get_current_user_required(request, async_db)
        
        # Should return user object
        assert hasattr(result, 'email')
        assert result.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_required_inactive_user(self, web_client, async_db):
        """Test get_current_user_required with inactive user."""
        from app.main_web import get_current_user_required
        from app.main_auth_async import create_access_token, User, UserRole, hash_password
        from fastapi import Request
        
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
        
        token = create_access_token(data={"sub": inactive_user.email})
        
        # Mock request with token for inactive user
        request = Mock(spec=Request)
        request.cookies = {"token": token}
        
        result = await get_current_user_required(request, async_db)
        
        # Should return redirect response
        assert hasattr(result, 'status_code')
        assert result.status_code == 302
    
    @pytest.mark.asyncio
    async def test_get_current_user_required_nonexistent_user(self, web_client, async_db):
        """Test get_current_user_required with nonexistent user."""
        from app.main_web import get_current_user_required
        from app.main_auth_async import create_access_token
        from fastapi import Request
        
        token = create_access_token(data={"sub": "nonexistent@example.com"})
        
        # Mock request with token for nonexistent user
        request = Mock(spec=Request)
        request.cookies = {"token": token}
        
        result = await get_current_user_required(request, async_db)
        
        # Should return redirect response
        assert hasattr(result, 'status_code')
        assert result.status_code == 302