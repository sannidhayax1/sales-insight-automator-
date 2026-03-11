"""
Sales Insight Automator - FastAPI Backend
Professional AI-powered sales data analyzer with secure endpoints
"""

import os
import logging
from typing import Optional
from datetime import datetime
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from dotenv import load_dotenv
import pandas as pd
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security & Rate Limiting
limiter = Limiter(key_func=get_remote_address)

# FastAPI app initialization with detailed documentation
app = FastAPI(
    title="Sales Insight Automator API",
    description="AI-powered sales data analyzer with secure file upload and AI-generated summaries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware with strict configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests", "detail": "Rate limit exceeded"}
    )

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "dev-key-change-in-production")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Initialize Gemini API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# ==================== Security Dependencies ====================

async def verify_api_key(x_api_key: str = None) -> bool:
    """Verify API key for protected endpoints"""
    if not x_api_key or x_api_key != API_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True

# ==================== Pydantic Models ====================

class UploadResponse(BaseModel):
    """Response model for file uploads"""
    status: str
    message: str
    summary_id: Optional[str] = None
    recipient_email: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str

# ==================== Helper Functions ====================

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max: {MAX_FILE_SIZE / 1024 / 1024}MB")
    
    # Check file extension
    allowed_extensions = [".csv", ".xlsx"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

async def parse_sales_data(file: UploadFile) -> pd.DataFrame:
    """Parse and validate sales data from CSV or XLSX"""
    try:
        contents = await file.read()
        
        if file.filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(contents))
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(BytesIO(contents))
        
        # Basic validation
        if df.empty:
            raise ValueError("File contains no data")
        
        return df
    
    except Exception as e:
        logger.error(f"Data parsing error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {str(e)}")

def generate_sales_summary(df: pd.DataFrame) -> str:
    """Generate AI-powered sales summary using Gemini"""
    try:
        # Prepare data context
        data_summary = f"""
        Sales Data Summary:
        - Total Records: {len(df)}
        - Date Range: {df.iloc[0]['Date'] if 'Date' in df.columns else 'N/A'} to {df.iloc[-1]['Date'] if 'Date' in df.columns else 'N/A'}
        - Total Revenue: ${df['Revenue'].sum():,.2f} if 'Revenue' in df.columns else 'N/A'
        
        Data Preview:
        {df.to_string()}
        
        Key Statistics:
        {df.describe().to_string()}
        """
        
        # Prepare prompt for Gemini
        prompt = f"""
        You are an expert business analyst. Analyze the following sales data and generate a 
        professional executive summary (300-400 words) suitable for leadership review. 
        Include key insights, trends, recommendations, and any red flags.
        
        {data_summary}
        
        Please provide:
        1. Executive Summary (2-3 paragraphs)
        2. Key Performance Indicators (3-4 bullet points)
        3. Risk Assessment (if applicable)
        4. Recommendations (3-4 bullet points)
        """
        
        # Call Gemini API
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        logger.error(f"AI summary generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

def send_summary_email(recipient_email: str, summary: str, filename: str) -> bool:
    """Send AI-generated summary via email"""
    try:
        # Create HTML email template
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #1f77d2;">Sales Insight Summary</h2>
                    <p><strong>File Analyzed:</strong> {filename}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <hr style="border: 1px solid #ddd;">
                    <div style="line-height: 1.6;">
                        {summary.replace(chr(10), '<br>')}
                    </div>
                    <hr style="border: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #666;">
                        This email was generated by Sales Insight Automator. 
                        Do not reply to this automated message.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Create email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Sales Insight Summary - {datetime.now().strftime('%B %Y')}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        
        msg.attach(MIMEText(summary, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Summary email sent to {recipient_email}")
        return True
    
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send summary email")

# ==================== API Endpoints ====================

@app.get("/health", tags=["Health"])
@limiter.limit("10/minute")
async def health_check(request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/v1/upload-and-summarize", response_model=UploadResponse, tags=["Sales Analysis"])
@limiter.limit("5/minute")
async def upload_and_summarize(
    request,
    file: UploadFile = File(...),
    recipient_email: str = Form(...)
) -> UploadResponse:
    """
    Upload sales data file and generate AI summary
    
    Parameters:
    - file: CSV or XLSX file with sales data
    - recipient_email: Email address for summary delivery
    
    Returns:
    - success: Boolean indicating operation success
    - message: Status message
    - summary_id: Unique identifier for the summary
    """
    
    try:
        # Validate inputs
        validate_file(file)
        
        # Basic email validation
        if not recipient_email or "@" not in recipient_email:
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Parse sales data
        df = await parse_sales_data(file)
        
        # Generate AI summary
        summary = generate_sales_summary(df)
        
        # Send email
        send_summary_email(recipient_email, summary, file.filename)
        
        # Generate summary ID
        summary_id = f"SUMM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Summary {summary_id} generated and sent to {recipient_email}")
        
        return UploadResponse(
            status="success",
            message=f"Summary generated and sent to {recipient_email}",
            summary_id=summary_id,
            recipient_email=recipient_email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle CORS preflight requests"""
    return {"status": "ok"}

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": "Sales Insight Automator API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
