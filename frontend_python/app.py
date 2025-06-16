"""
Python Frontend Server for Therapy Assistant Agent
FastAPI with Jinja2 templates - replacement for Node.js
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import requests
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Therapy Assistant Frontend",
    description="Web interface for Therapy Assistant Agent",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Backend API URL
BACKEND_URL = "http://localhost:8000"

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        # Get backend health status
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        backend_status = health_response.json() if health_response.status_code == 200 else {"status": "error"}
        
        # Get disorders list
        disorders_response = requests.get(f"{BACKEND_URL}/api/v1/disorders", timeout=5)
        disorders = disorders_response.json().get("disorders", []) if disorders_response.status_code == 200 else []
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "backend_status": backend_status,
            "disorders": disorders,
            "total_disorders": len(disorders)
        })
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Could not connect to backend API: {str(e)}"
        })

@app.get("/diagnostic", response_class=HTMLResponse)
async def diagnostic_tool(request: Request):
    """Diagnostic analysis tool page"""
    try:
        # Get disorders for dropdown
        disorders_response = requests.get(f"{BACKEND_URL}/api/v1/disorders", timeout=5)
        disorders = disorders_response.json().get("disorders", []) if disorders_response.status_code == 200 else []
        
        return templates.TemplateResponse("diagnostic.html", {
            "request": request,
            "disorders": disorders
        })
        
    except Exception as e:
        logger.error(f"Error loading diagnostic tool: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Could not load diagnostic tool: {str(e)}"
        })

@app.get("/cases", response_class=HTMLResponse)
async def clinical_cases(request: Request):
    """Clinical cases browser page"""
    try:
        # Get synthetic cases
        cases_response = requests.get(f"{BACKEND_URL}/api/v1/synthetic-cases", timeout=5)
        cases_data = cases_response.json() if cases_response.status_code == 200 else {}
        
        cases = cases_data.get("cases", [])
        total_cases = cases_data.get("total_cases", 0)
        
        return templates.TemplateResponse("cases.html", {
            "request": request,
            "cases": cases,
            "total_cases": total_cases,
            "sample_cases": len(cases)
        })
        
    except Exception as e:
        logger.error(f"Error loading clinical cases: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Could not load clinical cases: {str(e)}"
        })

@app.get("/disorders", response_class=HTMLResponse)
async def disorders_reference(request: Request):
    """Mental health disorders reference page"""
    try:
        # Get disorders with details
        disorders_response = requests.get(f"{BACKEND_URL}/api/v1/disorders", timeout=5)
        disorders_data = disorders_response.json() if disorders_response.status_code == 200 else {}
        
        disorders = disorders_data.get("disorders", [])
        
        # Group by category
        disorders_by_category = {}
        for disorder in disorders:
            category = disorder.get("category", "Other")
            if category not in disorders_by_category:
                disorders_by_category[category] = []
            disorders_by_category[category].append(disorder)
        
        return templates.TemplateResponse("disorders.html", {
            "request": request,
            "disorders_by_category": disorders_by_category,
            "total_disorders": len(disorders)
        })
        
    except Exception as e:
        logger.error(f"Error loading disorders reference: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Could not load disorders reference: {str(e)}"
        })

@app.get("/api/health")
async def frontend_health():
    """Frontend health check"""
    try:
        # Check backend connectivity
        backend_response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        backend_healthy = backend_response.status_code == 200
        
        return {
            "status": "healthy" if backend_healthy else "degraded",
            "frontend": "running",
            "backend_connectivity": "ok" if backend_healthy else "error",
            "backend_url": BACKEND_URL
        }
    except Exception as e:
        return {
            "status": "error",
            "frontend": "running", 
            "backend_connectivity": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)