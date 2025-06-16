# Server Access Guide

## ✅ Server Status: RUNNING

The Therapy Assistant Agent API is currently running on port 8000.

## 🌐 Try These URLs:

### Primary URLs:
- **http://127.0.0.1:8000/** - Main API (try this first!)
- **http://localhost:8000/** - Alternative localhost
- **http://0.0.0.0:8000/** - All interfaces

### Key Endpoints:
- **http://127.0.0.1:8000/health** - Health check
- **http://127.0.0.1:8000/docs** - Interactive API documentation
- **http://127.0.0.1:8000/api/v1/disorders** - Mental health disorders
- **http://127.0.0.1:8000/api/v1/synthetic-cases** - Clinical test cases

## 🔧 Troubleshooting:

### If Firefox can't connect:

1. **Try different browsers:**
   - Chrome: http://127.0.0.1:8000/
   - Safari: http://127.0.0.1:8000/
   - Edge: http://127.0.0.1:8000/

2. **Clear browser cache:**
   - Firefox: Ctrl+Shift+Delete
   - Chrome: Ctrl+Shift+Delete

3. **Check Firefox settings:**
   - Go to about:config
   - Search for "localhost"
   - Ensure network.proxy.allow_hijacking_localhost is true

4. **Disable Firefox proxy:**
   - Settings → Network Settings → No proxy

5. **Try curl/wget from terminal:**
   ```bash
   curl http://127.0.0.1:8000/health
   wget -qO- http://127.0.0.1:8000/health
   ```

## 📊 Server Verification:

Current server status:
- ✅ Process running (PID: 2498778)
- ✅ Port 8000 listening
- ✅ Health endpoint responding
- ✅ API endpoints functional

## 🚀 API Documentation:

Visit **http://127.0.0.1:8000/docs** for interactive API documentation with:
- Live endpoint testing
- Request/response examples
- Schema definitions
- Authentication details

## 📝 Available Data:

- **6 Mental Health Disorders** with DSM-5-TR and ICD-11 codes
- **30 Synthetic Clinical Cases** for testing
- **Database connectivity** testing
- **Health monitoring** endpoints