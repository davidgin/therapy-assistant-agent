#!/usr/bin/env python3
"""
Test ChromaDB setup and new Python frontend
"""

import sys
import os
import requests
import time
import subprocess
import signal

def test_chroma_backend():
    """Test ChromaDB backend server"""
    print("🧪 Testing ChromaDB Backend Server")
    print("-" * 40)
    
    # Start ChromaDB backend
    os.chdir('backend')
    os.environ['PYTHONPATH'] = os.getcwd()
    
    # Kill existing server
    os.system("pkill -f 'uvicorn.*8000'")
    time.sleep(2)
    
    # Start server
    backend_cmd = ['uvicorn', 'app.main_chroma:app', '--host', '0.0.0.0', '--port', '8000']
    backend_process = subprocess.Popen(backend_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("⏳ Starting ChromaDB backend server...")
    for i in range(15):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ ChromaDB backend server is running!")
                break
        except:
            time.sleep(1)
    else:
        print("❌ ChromaDB backend server failed to start")
        backend_process.terminate()
        return False, None
    
    # Test endpoints
    endpoints = [
        "/health",
        "/health/vector-db", 
        "/api/v1/disorders",
        "/api/v1/synthetic-cases"
    ]
    
    backend_results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend {endpoint}: {response.status_code}")
                backend_results.append(True)
            else:
                print(f"❌ Backend {endpoint}: {response.status_code}")
                backend_results.append(False)
        except Exception as e:
            print(f"❌ Backend {endpoint}: Error - {e}")
            backend_results.append(False)
    
    return all(backend_results), backend_process

def test_python_frontend():
    """Test Python frontend server"""
    print("\n🧪 Testing Python Frontend Server")
    print("-" * 40)
    
    os.chdir('../frontend_python')
    
    # Kill existing frontend
    os.system("pkill -f 'uvicorn.*3000'")
    time.sleep(2)
    
    # Start frontend server
    frontend_cmd = ['uvicorn', 'app:app', '--host', '0.0.0.0', '--port', '3000']
    frontend_process = subprocess.Popen(frontend_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("⏳ Starting Python frontend server...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:3000/", timeout=2)
            if response.status_code == 200:
                print("✅ Python frontend server is running!")
                break
        except:
            time.sleep(1)
    else:
        print("❌ Python frontend server failed to start")
        frontend_process.terminate()
        return False, None
    
    # Test frontend pages
    pages = [
        "/",
        "/api/health"
    ]
    
    frontend_results = []
    for page in pages:
        try:
            response = requests.get(f"http://localhost:3000{page}", timeout=5)
            if response.status_code == 200:
                print(f"✅ Frontend {page}: {response.status_code}")
                frontend_results.append(True)
            else:
                print(f"❌ Frontend {page}: {response.status_code}")
                frontend_results.append(False)
        except Exception as e:
            print(f"❌ Frontend {page}: Error - {e}")
            frontend_results.append(False)
    
    return all(frontend_results), frontend_process

def main():
    """Main test function"""
    print("🚀 Testing Complete Python Stack (ChromaDB + Python Frontend)")
    print("=" * 60)
    
    try:
        # Test backend
        backend_success, backend_process = test_chroma_backend()
        
        if not backend_success:
            print("\n❌ Backend tests failed. Stopping.")
            return False
        
        # Test frontend
        frontend_success, frontend_process = test_python_frontend()
        
        if backend_success and frontend_success:
            print("\n🎉 All tests passed!")
            print("\n📍 Servers running:")
            print("   • Backend (ChromaDB): http://localhost:8000")
            print("   • Frontend (Python): http://localhost:3000")
            print("   • API Docs: http://localhost:8000/docs")
            print("\n🔍 Test these URLs in your browser:")
            print("   • Dashboard: http://localhost:3000/")
            print("   • ChromaDB Health: http://localhost:8000/health/vector-db") 
            
            print("\n⚠️  Servers will keep running. Press Ctrl+C to stop.")
            
            # Keep servers running
            try:
                while True:
                    time.sleep(10)
                    # Check if servers are still running
                    if backend_process.poll() is not None:
                        print("❌ Backend process died")
                        break
                    if frontend_process.poll() is not None:
                        print("❌ Frontend process died")
                        break
            except KeyboardInterrupt:
                print("\n🛑 Stopping servers...")
        
        return backend_success and frontend_success
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        try:
            if 'backend_process' in locals():
                backend_process.terminate()
            if 'frontend_process' in locals():
                frontend_process.terminate()
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)