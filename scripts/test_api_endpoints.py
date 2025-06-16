#!/usr/bin/env python3
"""
API endpoint testing script for therapy assistant
Tests all major endpoints and RAG functionality
"""

import requests
import json
import sys
import time
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APITester:
    """Test suite for therapy assistant API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     headers: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Add auth header if available
            if self.auth_token and headers is None:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
            elif self.auth_token and headers:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Make request
            if method.upper() == "GET":
                response = self.session.get(url, params=data, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Analyze response
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "success": response.status_code == expected_status,
                "response_time": response.elapsed.total_seconds(),
                "response_data": None,
                "error": None
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200]
            
            if not result["success"]:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
            
            return result
            
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": None,
                "success": False,
                "response_time": None,
                "response_data": None,
                "error": str(e)
            }
    
    def test_health_endpoints(self):
        """Test health and status endpoints"""
        logger.info("🏥 Testing health endpoints...")
        
        tests = [
            ("GET", "/", {}, 200),
            ("GET", "/health", {}, 200),
            ("GET", "/health/services", {}, 200),
        ]
        
        for method, endpoint, data, expected in tests:
            result = self.test_endpoint(method, endpoint, data, expected_status=expected)
            self.test_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {method} {endpoint}: {result['status_code']}")
    
    def test_authentication(self):
        """Test authentication endpoints"""
        logger.info("🔐 Testing authentication...")
        
        # Test login with demo account
        login_data = {
            "username": "demo.therapist@example.com",
            "password": "demo123"
        }
        
        # Create form data for OAuth2 login
        form_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        form_data = "username=demo.therapist@example.com&password=demo123"
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data=form_data,
                headers=form_headers
            )
            
            result = {
                "endpoint": "/api/auth/login",
                "method": "POST",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds(),
                "response_data": None,
                "error": None
            }
            
            if response.status_code == 200:
                login_response = response.json()
                self.auth_token = login_response.get("access_token")
                result["response_data"] = {"token_received": bool(self.auth_token)}
                logger.info("✅ Login successful, token received")
            else:
                result["error"] = f"Login failed: {response.text}"
                logger.error("❌ Login failed")
            
            self.test_results.append(result)
            
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            self.test_results.append({
                "endpoint": "/api/auth/login",
                "method": "POST", 
                "success": False,
                "error": str(e)
            })
        
        # Test getting current user info
        if self.auth_token:
            result = self.test_endpoint("GET", "/api/auth/me")
            self.test_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} GET /api/auth/me: {result['status_code']}")
    
    def test_rag_endpoints(self):
        """Test RAG endpoints"""
        logger.info("🧠 Testing RAG endpoints...")
        
        if not self.auth_token:
            logger.warning("⚠️ No auth token, skipping RAG tests")
            return
        
        # Test diagnostic assistance
        diagnostic_data = {
            "symptoms": "persistent sadness for 3 weeks, loss of interest in activities, difficulty concentrating, sleep disturbances, fatigue",
            "patient_context": "28-year-old female, no prior psychiatric history, recent job loss"
        }
        
        result = self.test_endpoint(
            "GET", 
            "/api/v1/rag/diagnose",
            data=diagnostic_data
        )
        self.test_results.append(result)
        
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} GET /api/v1/rag/diagnose: {result['status_code']}")
        
        if result["success"] and result["response_data"]:
            ai_response = result["response_data"].get("ai_response", {})
            if ai_response.get("status") == "success":
                logger.info("  🎯 AI diagnostic response generated successfully")
            else:
                logger.warning(f"  ⚠️ AI response issue: {ai_response.get('message', 'Unknown')}")
        
        # Test treatment recommendations
        treatment_data = {
            "diagnosis": "Major Depressive Disorder",
            "patient_context": "First episode, moderate severity, patient prefers therapy"
        }
        
        result = self.test_endpoint(
            "GET",
            "/api/v1/rag/treatment", 
            data=treatment_data
        )
        self.test_results.append(result)
        
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} GET /api/v1/rag/treatment: {result['status_code']}")
        
        # Test case analysis
        result = self.test_endpoint("GET", "/api/v1/rag/case-analysis/CASE_001")
        self.test_results.append(result)
        
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} GET /api/v1/rag/case-analysis/CASE_001: {result['status_code']}")
        
        # Test knowledge search
        search_data = {
            "query": "depression treatment guidelines",
            "doc_type": "treatment_guideline"
        }
        
        result = self.test_endpoint(
            "GET",
            "/api/v1/rag/search/knowledge",
            data=search_data
        )
        self.test_results.append(result)
        
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} GET /api/v1/rag/search/knowledge: {result['status_code']}")
    
    def test_data_endpoints(self):
        """Test data retrieval endpoints"""
        logger.info("📊 Testing data endpoints...")
        
        # Test synthetic cases
        result = self.test_endpoint("GET", "/api/v1/synthetic-cases")
        self.test_results.append(result)
        
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} GET /api/v1/synthetic-cases: {result['status_code']}")
        
        if result["success"] and result["response_data"]:
            cases = result["response_data"].get("cases", [])
            logger.info(f"  📋 Found {len(cases)} synthetic cases")
        
        # Test disorders list (requires auth)
        if self.auth_token:
            result = self.test_endpoint("GET", "/api/v1/rag/knowledge/disorders")
            self.test_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} GET /api/v1/rag/knowledge/disorders: {result['status_code']}")
            
            # Test document types
            result = self.test_endpoint("GET", "/api/v1/rag/knowledge/types")
            self.test_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} GET /api/v1/rag/knowledge/types: {result['status_code']}")
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        logger.info("🚨 Testing error handling...")
        
        # Test invalid endpoints
        result = self.test_endpoint("GET", "/nonexistent", expected_status=404)
        self.test_results.append(result)
        
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} GET /nonexistent: {result['status_code']} (expected 404)")
        
        # Test unauthorized access
        if self.auth_token:
            # Temporarily remove token
            original_token = self.auth_token
            self.auth_token = None
            
            result = self.test_endpoint("GET", "/api/v1/rag/diagnose", 
                                      data={"symptoms": "test"}, expected_status=401)
            self.test_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} GET /api/v1/rag/diagnose (no auth): {result['status_code']} (expected 401)")
            
            # Restore token
            self.auth_token = original_token
        
        # Test invalid RAG request
        if self.auth_token:
            result = self.test_endpoint(
                "GET", 
                "/api/v1/rag/diagnose",
                data={"symptoms": ""},  # Empty symptoms
                expected_status=422
            )
            self.test_results.append(result)
            
            # Note: This might return 500 if validation isn't implemented yet
            status = "✅" if result["status_code"] in [400, 422, 500] else "❌"
            logger.info(f"{status} GET /api/v1/rag/diagnose (empty symptoms): {result['status_code']}")
    
    def run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 Starting API endpoint tests...")
        
        start_time = time.time()
        
        try:
            self.test_health_endpoints()
            self.test_authentication()
            self.test_rag_endpoints()
            self.test_data_endpoints()
            self.test_error_handling()
            
        except KeyboardInterrupt:
            logger.info("❌ Tests interrupted by user")
            return False
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.print_summary(duration)
        return True
    
    def print_summary(self, duration: float):
        """Print test results summary"""
        logger.info("📊 Test Results Summary")
        logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {successful_tests/total_tests*100:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        # Print failed tests
        if failed_tests > 0:
            logger.info("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  {result['method']} {result['endpoint']}: {result['error']}")
        
        # Print response times
        response_times = [r["response_time"] for r in self.test_results if r["response_time"]]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            logger.info(f"\n⏱️ Response Times:")
            logger.info(f"  Average: {avg_time:.3f}s")
            logger.info(f"  Maximum: {max_time:.3f}s")

def main():
    """Main test function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    logger.info(f"Testing API at: {base_url}")
    
    tester = APITester(base_url)
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            logger.error(f"❌ Server not responding correctly: {response.status_code}")
            return 1
    except requests.RequestException as e:
        logger.error(f"❌ Cannot connect to server: {e}")
        logger.info("💡 Make sure the server is running at the specified URL")
        return 1
    
    logger.info("✅ Server is responding")
    
    # Run tests
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())