"""
Cold Email API - REST API for sending cold emails
Run with: python api.py
API docs available at: http://localhost:8000/docs
"""

import smtplib
import os
import requests
import pandas as pd
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Cold Email API",
    description="API for sending personalized cold emails for job applications",
    version="1.0.0"
)

# Allow CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gmail credentials (optional - users can provide their own)
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

# Default email template
DEFAULT_SUBJECT = "Application for SDE-1 Position at {company_name}"
DEFAULT_BODY = """Dear {hr_name},

I hope this email finds you well. I am writing to express my interest in the Software Developer Engineer (SDE-1) position at {company_name}.

I am a passionate software developer with strong problem-solving skills and experience in:
• Data Structures & Algorithms
• Python, Java, JavaScript
• Web Development (React, Node.js)
• Database Management (SQL, MongoDB)
• Git and Version Control

I am eager to contribute to {company_name}'s innovative projects and would be grateful for the opportunity to discuss how my skills align with your team's needs.

Thank you for your time and consideration.

Best regards,
[Your Name]
Email: {sender_email}
"""


# ========== Pydantic Models ==========

class SingleEmailRequest(BaseModel):
    to_email: str
    hr_name: str
    company_name: str
    subject: Optional[str] = None
    body: Optional[str] = None
    # User's own credentials (optional - falls back to .env)
    sender_email: Optional[str] = None
    sender_password: Optional[str] = None

class GoogleSheetRequest(BaseModel):
    sheet_url: str
    subject: Optional[str] = None
    body: Optional[str] = None

class Contact(BaseModel):
    email: str
    hr_name: str
    company_name: str

class EmailPreview(BaseModel):
    to_email: str
    subject: str
    body: str

class SendResult(BaseModel):
    success: bool
    message: str
    email: str


# ========== Helper Functions ==========

def fetch_google_sheet(sheet_url: str) -> str:
    """Fetch data from a Google Sheet URL as CSV."""
    if '/d/' in sheet_url:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    else:
        sheet_id = sheet_url
    
    gid = '0'
    if 'gid=' in sheet_url:
        gid = sheet_url.split('gid=')[1].split('#')[0].split('&')[0]
    
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    response = requests.get(export_url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch Google Sheet")
    
    return response.text


def parse_contacts(csv_data: str) -> List[dict]:
    """Parse CSV data and extract contacts."""
    df = pd.read_csv(StringIO(csv_data), header=None)
    
    contacts = []
    for _, row in df.iterrows():
        values = [str(val).strip() for val in row if pd.notna(val) and str(val).strip()]
        
        if len(values) >= 2:
            company = values[0] if len(values) > 0 else "Your Company"
            
            email = None
            for val in values:
                if '@' in val:
                    email = val
                    break
            
            name = values[-1] if values[-1] != email else "Hiring Manager"
            
            if email:
                contacts.append({
                    'email': email,
                    'hr_name': name,
                    'company_name': company
                })
    
    return contacts


def send_email(to_email: str, subject: str, body: str, sender_email: str = None, sender_password: str = None) -> bool:
    """Send an email via Gmail SMTP."""
    # Use provided credentials or fall back to .env
    gmail_addr = sender_email or GMAIL_ADDRESS
    gmail_pass = sender_password or GMAIL_APP_PASSWORD
    
    if not gmail_addr or not gmail_pass:
        raise HTTPException(status_code=400, detail="Gmail credentials required. Please provide your email and app password.")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = gmail_addr
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_addr, gmail_pass)
            server.send_message(msg)
        
        return True
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=401, detail="Gmail authentication failed. Check your email and app password.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


# ========== API Endpoints ==========

@app.get("/")
def root():
    """API root - shows available endpoints."""
    return {
        "message": "Cold Email API",
        "endpoints": {
            "docs": "/docs - Interactive API documentation",
            "send_single": "POST /send - Send email to one person",
            "send_from_sheet": "POST /send-from-sheet - Send to all contacts in Google Sheet",
            "preview": "POST /preview - Preview email without sending",
            "fetch_contacts": "POST /fetch-contacts - Get contacts from Google Sheet",
            "health": "GET /health - Check API status"
        }
    }


@app.get("/health")
def health_check():
    """Check if API is running and configured."""
    return {
        "status": "ok",
        "gmail_configured": bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD),
        "gmail_address": GMAIL_ADDRESS
    }


@app.post("/preview", response_model=EmailPreview)
def preview_email(request: SingleEmailRequest):
    """Preview an email without sending it."""
    sender = request.sender_email or GMAIL_ADDRESS or "your.email@gmail.com"
    subject = (request.subject or DEFAULT_SUBJECT).format(
        company_name=request.company_name,
        hr_name=request.hr_name
    )
    body = (request.body or DEFAULT_BODY).format(
        company_name=request.company_name,
        hr_name=request.hr_name,
        sender_email=sender
    )
    
    return EmailPreview(
        to_email=request.to_email,
        subject=subject,
        body=body
    )


@app.post("/send", response_model=SendResult)
def send_single_email(request: SingleEmailRequest):
    """Send an email to a single recipient. Users can provide their own Gmail credentials."""
    sender = request.sender_email or GMAIL_ADDRESS
    password = request.sender_password or GMAIL_APP_PASSWORD
    
    if not sender or not password:
        raise HTTPException(status_code=400, detail="Please provide your Gmail address and App Password")
    
    subject = (request.subject or DEFAULT_SUBJECT).format(
        company_name=request.company_name,
        hr_name=request.hr_name
    )
    body = (request.body or DEFAULT_BODY).format(
        company_name=request.company_name,
        hr_name=request.hr_name,
        sender_email=sender
    )
    
    send_email(request.to_email, subject, body, sender, password)
    
    return SendResult(
        success=True,
        message=f"Email sent to {request.hr_name} at {request.company_name}",
        email=request.to_email
    )


@app.post("/fetch-contacts", response_model=List[Contact])
def fetch_contacts(request: GoogleSheetRequest):
    """Fetch and parse contacts from a Google Sheet."""
    csv_data = fetch_google_sheet(request.sheet_url)
    contacts = parse_contacts(csv_data)
    
    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found in the sheet")
    
    return [Contact(**c) for c in contacts]


@app.post("/send-from-sheet")
def send_from_google_sheet(request: GoogleSheetRequest):
    """Send emails to all contacts in a Google Sheet."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise HTTPException(status_code=500, detail="Gmail credentials not configured")
    
    csv_data = fetch_google_sheet(request.sheet_url)
    contacts = parse_contacts(csv_data)
    
    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found in the sheet")
    
    results = []
    for contact in contacts:
        subject = (request.subject or DEFAULT_SUBJECT).format(
            company_name=contact['company_name'],
            hr_name=contact['hr_name']
        )
        body = (request.body or DEFAULT_BODY).format(
            company_name=contact['company_name'],
            hr_name=contact['hr_name'],
            sender_email=GMAIL_ADDRESS
        )
        
        try:
            send_email(contact['email'], subject, body)
            results.append({
                "success": True,
                "email": contact['email'],
                "name": contact['hr_name'],
                "company": contact['company_name']
            })
        except Exception as e:
            results.append({
                "success": False,
                "email": contact['email'],
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r['success'])
    
    return {
        "total": len(contacts),
        "success": success_count,
        "failed": len(contacts) - success_count,
        "results": results
    }


# Serve the frontend HTML
@app.get("/app")
def serve_app():
    """Serve the Cold Email Sender web app."""
    return FileResponse("index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "="*50)
    print("  Cold Email API")
    print("="*50)
    print(f"  Web App: http://localhost:{port}/app")
    print(f"  API Docs: http://localhost:{port}/docs")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
