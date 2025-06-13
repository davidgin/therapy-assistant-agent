#!/usr/bin/env python3
"""
Test the FastAPI server locally
"""

import sys
import os
import requests
import time
import subprocess
import signal
from threading import Thread

def start_server():
    """Start the FastAPI server"""
    os.chdir('backend')
    os.environ['PYTHONPATH'] = os.getcwd()
    
    # Start server
    cmd = ['uvicorn', 'app.main_simple:app', '--host', '0.0.0.0', '--port', '8000']
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def test_endpoints():
    """Test server endpoints"""
    base_url = "http://localhost:8000"
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is running!")
                break
        except:
            time.sleep(1)
    else:
        print("❌ Server failed to start")
        return False
    
    # Test endpoints
    endpoints = [
        "/",
        "/health", 
        "/health/database",
        "/api/v1/disorders",
        "/api/v1/synthetic-cases"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: {response.status_code}")
                results.append(True)
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
            results.append(False)
    
    return all(results)

def main():
    """Main test function"""
    print("🧪 Testing Therapy Assistant Agent API")
    print("=" * 50)
    
    # Start server
    server_process = start_server()
    
    try:
        # Test endpoints
        success = test_endpoints()
        
        if success:
            print("\n🎉 All endpoints working!")
            print("\n📍 Server URLs:")
            print("   • Main API: http://localhost:8000")
            print("   • Health: http://localhost:8000/health")
            print("   • API Docs: http://localhost:8000/docs")
            print("   • Disorders: http://localhost:8000/api/v1/disorders")
            print("   • Sample Cases: http://localhost:8000/api/v1/synthetic-cases")
            print("\n🚀 Ready for frontend development!")
        else:
            print("\n❌ Some endpoints failed")
        
        return success
        
    finally:
        # Clean up
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)