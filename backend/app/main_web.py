"""
FastAPI web application with server-side rendering (no React/Node.js)
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
import logging
from datetime import timedelta
from typing import Optional
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import secrets
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import from existing modules
from .main_auth_async import (
    User, UserRole, LicenseType, AsyncSessionLocal, get_async_db,
    hash_password, verify_password, create_access_token, decode_token,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Async OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Therapy Assistant Web Application...")
    
    # Create database tables and demo users (reuse from main_auth_async)
    from .main_auth_async import lifespan as auth_lifespan
    async with auth_lifespan(app):
        yield
    
    logger.info("Shutting down Therapy Assistant Web Application...")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Therapy Assistant Web Application",
    description="AI-powered diagnostic and treatment support - Web Interface",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS (minimal since we're serving everything from FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="backend/app/templates")

# Session management (simple cookie-based)
from fastapi import Cookie
from fastapi.responses import Response

def get_current_user_from_cookie(token: Optional[str] = Cookie(None)):
    """Get current user from session cookie"""
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    return payload.get("sub")  # email

async def get_current_user_required(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Get current user or redirect to login"""
    token = request.cookies.get("token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    
    payload = decode_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=302)
    
    email = payload.get("sub")
    if not email:
        return RedirectResponse(url="/login", status_code=302)
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return RedirectResponse(url="/login", status_code=302)
    
    return user

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirect to dashboard if logged in, otherwise show login"""
    user_email = get_current_user_from_cookie(request.cookies.get("token"))
    
    if user_email:
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
@limiter.limit("5/minute")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Handle login form submission"""
    try:
        # Authenticate user
        result = await db.execute(select(User).where(User.email == username))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Invalid email or password"}
            )
        
        if not user.is_active:
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Account is inactive"}
            )
        
        # Create session token
        access_token = create_access_token(data={"sub": user.email})
        
        # Redirect to dashboard with cookie
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=False  # Set to True in production with HTTPS
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Login failed. Please try again."}
        )

@app.get("/logout")
async def logout():
    """Logout and clear session"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Dashboard page"""
    user = await get_current_user_required(request, db)
    if isinstance(user, RedirectResponse):
        return user
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "user": user,
            "openai_available": openai_client is not None
        }
    )

@app.get("/diagnostic", response_class=HTMLResponse)
async def diagnostic_page(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Diagnostic assistant page"""
    user = await get_current_user_required(request, db)
    if isinstance(user, RedirectResponse):
        return user
    
    return templates.TemplateResponse(
        "diagnostic.html", 
        {"request": request, "user": user}
    )

@app.post("/diagnostic")
@limiter.limit("10/minute")
async def diagnostic_post(
    request: Request,
    symptoms: str = Form(...),
    patient_context: str = Form(""),
    db: AsyncSession = Depends(get_async_db)
):
    """Handle diagnostic form submission"""
    user = await get_current_user_required(request, db)
    if isinstance(user, RedirectResponse):
        return user
    
    if not openai_client:
        return templates.TemplateResponse(
            "diagnostic.html", 
            {
                "request": request, 
                "user": user,
                "error": "AI service not available"
            }
        )
    
    try:
        # Create diagnostic prompt
        prompt = f"""You are an expert clinical psychologist providing diagnostic assistance based on DSM-5-TR criteria.

Patient Symptoms: {symptoms}
Patient Context: {patient_context}

Please provide a professional clinical analysis including:
1. **Primary Differential Diagnoses** (list 2-3 most likely diagnoses with DSM-5-TR codes)
2. **Clinical Reasoning** (explain why these diagnoses are being considered)
3. **Additional Assessment Recommendations** (what further evaluation is needed)
4. **Risk Factors** (any immediate concerns or risk factors to consider)

Important: This is for educational and clinical support purposes only. All final diagnostic decisions must be made by qualified mental health professionals through comprehensive clinical assessment.

Provide a structured, evidence-based response."""

        # Call OpenAI API
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a clinical psychology expert providing diagnostic assistance based on DSM-5-TR criteria."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        return templates.TemplateResponse(
            "diagnostic.html", 
            {
                "request": request, 
                "user": user,
                "symptoms": symptoms,
                "patient_context": patient_context,
                "ai_response": ai_response,
                "success": True
            }
        )
        
    except Exception as e:
        logger.error(f"Diagnostic error: {e}")
        return templates.TemplateResponse(
            "diagnostic.html", 
            {
                "request": request, 
                "user": user,
                "symptoms": symptoms,
                "patient_context": patient_context,
                "error": f"AI service error: {str(e)}"
            }
        )

@app.get("/treatment", response_class=HTMLResponse)
async def treatment_page(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Treatment planning page"""
    user = await get_current_user_required(request, db)
    if isinstance(user, RedirectResponse):
        return user
    
    return templates.TemplateResponse(
        "treatment.html", 
        {"request": request, "user": user}
    )

@app.post("/treatment")
@limiter.limit("10/minute")
async def treatment_post(
    request: Request,
    diagnosis: str = Form(...),
    patient_context: str = Form(""),
    db: AsyncSession = Depends(get_async_db)
):
    """Handle treatment planning form submission"""
    user = await get_current_user_required(request, db)
    if isinstance(user, RedirectResponse):
        return user
    
    if not openai_client:
        return templates.TemplateResponse(
            "treatment.html", 
            {
                "request": request, 
                "user": user,
                "error": "AI service not available"
            }
        )
    
    try:
        prompt = f"""You are an expert clinical psychologist providing evidence-based treatment recommendations.

Diagnosis: {diagnosis}
Patient Context: {patient_context}

Please provide comprehensive treatment recommendations including:
1. **Primary Treatment Approaches** (evidence-based therapies most effective for this diagnosis)
2. **Treatment Goals** (specific, measurable therapeutic objectives)
3. **Intervention Strategies** (specific techniques and approaches)
4. **Timeline and Frequency** (recommended session frequency and duration)
5. **Potential Challenges** (common obstacles and how to address them)
6. **Outcome Measures** (how to track progress)

Important: All treatment must be provided by qualified mental health professionals. This is for educational and clinical support purposes only.

Provide structured, evidence-based recommendations following best practices."""

        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a clinical psychology expert providing evidence-based treatment recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        
        ai_response = response.choices[0].message.content
        
        return templates.TemplateResponse(
            "treatment.html", 
            {
                "request": request, 
                "user": user,
                "diagnosis": diagnosis,
                "patient_context": patient_context,
                "ai_response": ai_response,
                "success": True
            }
        )
        
    except Exception as e:
        logger.error(f"Treatment error: {e}")
        return templates.TemplateResponse(
            "treatment.html", 
            {
                "request": request, 
                "user": user,
                "diagnosis": diagnosis,
                "patient_context": patient_context,
                "error": f"AI service error: {str(e)}"
            }
        )

@app.get("/cases", response_class=HTMLResponse)
async def cases_page(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Case analysis page"""
    user = await get_current_user_required(request, db)
    if isinstance(user, RedirectResponse):
        return user
    
    # Load synthetic cases
    try:
        from .services.async_file_service import load_synthetic_cases
        cases = await load_synthetic_cases()
    except Exception as e:
        logger.error(f"Error loading cases: {e}")
        cases = []
    
    return templates.TemplateResponse(
        "cases.html", 
        {
            "request": request, 
            "user": user,
            "cases": cases[:10]  # Show first 10 cases
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "message": "FastAPI Web Application is running",
        "openai_available": openai_client is not None
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "error": "Page not found", "status_code": 404}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)