# ==========================================================
# RegulaAI – AI Powered Regulatory Compliance System
# ==========================================================

import streamlit as st
import PyPDF2
import os
import io
import re
import smtplib
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from groq import Groq
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from dotenv import load_dotenv

# Try to import docx, install if not available
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Load environment
load_dotenv()

# Get API keys
GROQ_KEY = os.getenv("GROQ_API_KEY")
EMAIL_SENDER = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("SENDER_PASSWORD")

# Initialize Groq client
if GROQ_KEY:
    try:
        client = Groq(api_key=GROQ_KEY)
    except:
        import httpx
        client = Groq(api_key=GROQ_KEY, http_client=httpx.Client())
else:
    client = None

# ==========================================================
# CLAUSE DEFINITIONS
# ==========================================================

CLAUSE_PATTERNS = {
    "Confidentiality": {
        "patterns": [
            r'confidential(?:ity)?\s+(?:agreement|clause|obligation)',
            r'non-?disclosure',
            r'proprietary\s+information',
            r'secret',
            r'private\s+information'
        ],
        "risk": "medium",
        "description": "Controls how confidential information is handled"
    },
    "Termination": {
        "patterns": [
            r'terminat(?:ion|e|es)\s+(?:clause|condition|right)',
            r'end\s+of\s+(?:agreement|contract)',
            r'cancel(?:lation)?',
            r'breach\s+of\s+contract'
        ],
        "risk": "high",
        "description": "Defines conditions under which contract can be ended"
    },
    "Payment Terms": {
        "patterns": [
            r'payment\s+(?:terms|condition|schedule)',
            r'fee\s+(?:structure|schedule)',
            r'invoice',
            r'compensation',
            r'price\s+and\s+payment'
        ],
        "risk": "high",
        "description": "Specifies payment amounts, timing, and methods"
    },
    "Liability": {
        "patterns": [
            r'liability\s+(?:clause|limitation|limit)',
            r'limit\s+of\s+liability',
            r'damages',
            r'indemnif',
            r'liquidated\s+damages'
        ],
        "risk": "high",
        "description": "Limits or defines financial responsibilities"
    },
    "Intellectual Property": {
        "patterns": [
            r'intellectual\s+property',
            r'i\.?p\s+rights',
            r'patent\s+and\s+copyright',
            r'trade\s+secret',
            r'ownership\s+of\s+(?:rights|property)'
        ],
        "risk": "medium",
        "description": "Defines ownership of creative works and inventions"
    },
    "Dispute Resolution": {
        "patterns": [
            r'dispute\s+resolution',
            r'arbitration',
            r'governing\s+law',
            r'jurisdiction',
            r'legal\s+proceedings'
        ],
        "risk": "medium",
        "description": "Defines how conflicts will be resolved"
    },
    "Force Majeure": {
        "patterns": [
            r'force\s+majeure',
            r'act\s+of\s+god',
            r'unforeseeable\s+circumstances',
            r'natural\s+disaster'
        ],
        "risk": "low",
        "description": "Excuses performance due to extraordinary events"
    },
    "Warranty": {
        "patterns": [
            r'warrant(?:y|ies)?\s+(?:clause|statement)',
            r'guarantee',
            r'representation',
            r'declaration\s+of'
        ],
        "risk": "medium",
        "description": "Promises about quality or performance"
    },
    "Assignment": {
        "patterns": [
            r'assign(?:ment)?\s+(?:clause|right|restriction)',
            r'transfer\s+of\s+rights',
            r'successor\s+and\s+assigns'
        ],
        "risk": "low",
        "description": "Controls transfer of contractual rights"
    },
    "Indemnification": {
        "patterns": [
            r'indemnif(?:y|ication)\s+(?:clause|obligation)',
            r'hold\s+harmless',
            r'defense\s+and\s+indemnification'
        ],
        "risk": "high",
        "description": "Requires one party to cover losses of another"
    },
    "Notices": {
        "patterns": [
            r'notice\s+(?:clause|requirement|provision)',
            r'communication\s+(?:clause|method)',
            r'written\s+notice'
        ],
        "risk": "low",
        "description": "Defines how formal communications are sent"
    },
    "Entire Agreement": {
        "patterns": [
            r'entire\s+agreement\s+clause',
            r'whole\s+agreement',
            r'merger\s+clause',
            r'supersedes\s+all'
        ],
        "risk": "low",
        "description": "States contract contains all terms"
    }
}

# Risk level colors and icons
RISK_CONFIG = {
    "high": {"color": "🔴", "level": "High Risk", "score": 75},
    "medium": {"color": "🟠", "level": "Medium Risk", "score": 50},
    "low": {"color": "🟢", "level": "Low Risk", "score": 25},
    "missing": {"color": "⚪", "level": "Missing Clause", "score": 0}
}

# ==========================================================
# SESSION STATE INITIALIZATION
# ==========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "contract_text" not in st.session_state:
    st.session_state.contract_text = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "improved_contract" not in st.session_state:
    st.session_state.improved_contract = ""

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# ==========================================================
# LOGIN/LOGOUT FUNCTIONS
# ==========================================================

def login_page():
    # Custom CSS for modern login page
    st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        min-height: 100vh;
    }
    
    /* Login Card Container */
    .login-card {
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        padding: 40px;
        max-width: 420px;
        margin: 0 auto;
    }
    
    /* Logo Style */
    .app-logo {
        text-align: center;
        margin-bottom: 20px;
    }
    .app-logo img {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Title Styles */
    .login-title {
        color: #1a1a2e;
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    .login-subtitle {
        color: #666;
        text-align: center;
        font-size: 14px;
        margin-bottom: 30px;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 12px 15px;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Checkbox Styles */
    .stCheckbox > label {
        color: #555;
        font-size: 14px;
    }
    
    /* Link Styles */
    .forgot-password {
        color: #667eea;
        text-decoration: none;
        font-size: 14px;
        float: right;
    }
    .forgot-password:hover {
        text-decoration: underline;
    }
    
    /* Login Button */
    .login-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px;
        font-size: 16px;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 10px;
    }
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Social Login */
    .social-divider {
        text-align: center;
        margin: 25px 0;
        position: relative;
    }
    .social-divider::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #e0e0e0;
    }
    .social-divider span {
        background: white;
        padding: 0 15px;
        color: #888;
        font-size: 13px;
        position: relative;
    }
    
    /* Social Buttons */
    .social-button {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 12px;
        font-size: 14px;
        font-weight: 500;
        color: #333;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
    }
    .social-button:hover {
        border-color: #667eea;
        background: #f8f9ff;
    }
    
    /* Remember Me Row */
    .remember-forgot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 15px 0;
    }
    
    /* Footer */
    .login-footer {
        text-align: center;
        margin-top: 25px;
        color: #888;
        font-size: 13px;
    }
    
    /* Error Message */
    .error-message {
        background: #fee;
        border: 1px solid #fcc;
        color: #c33;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 15px;
        font-size: 14px;
    }
    
    /* Success Message */
    .success-message {
        background: #efe;
        border: 1px solid #cfc;
        color: #3c3;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 15px;
        font-size: 14px;
    }
    
    /* Loading Animation */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check for session message
    if 'login_message' in st.session_state:
        if st.session_state.get('login_message_type') == 'error':
            st.markdown(f"""<div class="error-message">⚠️ {st.session_state.login_message}</div>""", unsafe_allow_html=True)
        elif st.session_state.get('login_message_type') == 'success':
            st.markdown(f"""<div class="success-message">✅ {st.session_state.login_message}</div>""", unsafe_allow_html=True)
        # Clear the message
        del st.session_state['login_message']
        del st.session_state['login_message_type']
    
    # Login Card Container
    with st.container():
        # Center the card
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Login Card
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            
            # App Logo with Gradient Text
            st.markdown("""
            <div class="app-logo">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#667eea"/>
                            <stop offset="100%" style="stop-color:#764ba2"/>
                        </linearGradient>
                    </defs>
                    <circle cx="40" cy="40" r="38" fill="url(#logoGradient)"/>
                    <path d="M25 35h30M25 45h20M25 55h25" stroke="white" stroke-width="3" stroke-linecap="round"/>
                    <circle cx="55" cy="30" r="8" fill="white" opacity="0.3"/>
                </svg>
            </div>
            <!-- Stylish Gradient RegulaAI Text -->
            <h1 style="text-align: center; margin: 20px 0 5px 0;">
                <span style="
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 42px;
                    font-weight: 800;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    text-shadow: 0px 4px 8px rgba(102, 126, 234, 0.3);
                    letter-spacing: 2px;
                ">RegulaAI</span>
            </h1>
            <p style="text-align: center; color: #666; font-size: 13px; margin-bottom: 25px; letter-spacing: 1px;">
                AI-Powered Regulatory Compliance
            </p>
            """, unsafe_allow_html=True)
            
            # Login Form
            with st.form("login_form", clear_on_submit=True):
                # Email Input
                email = st.text_input("📧 Email / Username", placeholder="Enter your email address", 
                                     help="Enter your registered email")
                
                # Password Input
                password = st.text_input("🔑 Password", type="password", 
                                       placeholder="Enter your password",
                                       help="Enter your password")
                
                # Remember Me and Forgot Password Row
                col_rem, col_forg = st.columns([1, 1])
                with col_rem:
                    remember_me = st.checkbox("☑ Remember Me")
                with col_forg:
                    st.markdown('<a href="#" class="forgot-password">Forgot Password?</a>', 
                              unsafe_allow_html=True)
                
                # Login Button with loading
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.session_state.login_message = "Please enter both email and password"
                        st.session_state.login_message_type = "error"
                        st.rerun()
                    elif "@" not in email:
                        st.session_state.login_message = "Please enter a valid email address"
                        st.session_state.login_message_type = "error"
                        st.rerun()
                    elif len(password) < 6:
                        st.session_state.login_message = "Password must be at least 6 characters"
                        st.session_state.login_message_type = "error"
                        st.rerun()
                    else:
                        # Simulate loading
                        with st.spinner(""):
                            st.markdown('<div class="loading-spinner"></div>', unsafe_allow_html=True)
                            import time
                            time.sleep(1.5)
                        
                        # Successful login
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.remember_me = remember_me
                        st.session_state.login_message = "Login successful! Redirecting..."
                        st.session_state.login_message_type = "success"
                        st.rerun()
            
            # Social Login Divider
            st.markdown("""
            <div class="social-divider">
                <span>or continue with</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Social Login Buttons
            col_google, col_github = st.columns(2)
            with col_google:
                st.markdown("""
                <button class="social-button" disabled>
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                        <path d="M17.5 9.25c0-.81-.07-1.59-.19-2.33H9v4.42h4.72c-.2 1.08-.82 2-1.73 2.61v2.18h2.81c1.63-1.5 2.81-3.71 2.81-6.38z" fill="#4285F4"/>
                        <path d="M9 16.5c2.24 0 4.11-.74 5.47-2.01l-2.81-2.18c-.74.5-1.69.79-2.66.79-2.05 0-3.79-1.39-4.41-3.26H.91v2.25C2.45 14.92 5.41 16.5 9 16.5z" fill="#34A853"/>
                        <path d="M4.59 10.67c-.22-.66-.35-1.36-.35-2.17s.13-1.51.35-2.17V5.93H.91C.32 7.08 0 8.5 0 10s.32 2.92.91 4.07l2.68-2.4z" fill="#FBBC05"/>
                        <path d="M9 3.53c1.17 0 2.22.4 3.04 1.2l2.73-2.73C13.11.89 11.24 0 9 0 5.41 0 2.45 1.58.91 3.93l2.68 2.4C5.21 4.92 6.95 3.53 9 3.53z" fill="#EA4335"/>
                    </svg>
                    Google
                </button>
                """, unsafe_allow_html=True)
            
            with col_github:
                st.markdown("""
                <button class="social-button" disabled>
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="#333">
                        <path d="M9 0C4.03 0 0 4.03 0 9c0 3.96 2.56 7.32 6.11 8.52.45.08.62-.2.62-.44v-1.32c-2.48.55-3.01-1.2-3.01-1.2-.41-1.04-1.01-1.32-1.01-1.32-.82-.56.06-.55.06-.55.91.07 1.39.94 1.39.94.81 1.39 2.12.99 2.64.76.08-.59.32-.99.58-1.22-2.01-.23-4.12-1-4.12-4.46 0-.98.35-1.79.93-2.42-.09-.23-.4-1.15.09-2.39 0 0 .76-.24 2.48.93.72-.2 1.49-.3 2.26-.3.77 0 1.54.1 2.26.3 1.72-1.17 2.48-.93 2.48-.93.49 1.24.18 2.16.09 2.39.58.63.93 1.44.93 2.42 0 3.46-2.11 4.23-4.13 4.46.33.28.61.83.61 1.67v2.47c0 .25.17.53.63.44C15.44 16.32 18 13.46 18 9c0-4.97-4.03-9-9-9z"/>
                    </svg>
                    GitHub
                </button>
                """, unsafe_allow_html=True)
            
            # Footer
            st.markdown("""
            <div class="login-footer">
                🔒 Secure Login | RegulaAI v1.0
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

def logout():
    st.session_state.logged_in = False
    st.session_state.contract_text = ""
    st.session_state.chat_history = []
    st.session_state.improved_contract = ""
    st.session_state.analysis_results = None
    st.rerun()

# ==========================================================
# FILE EXTRACTION FUNCTIONS
# ==========================================================

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error: {str(e)}"

def extract_text_from_docx(file):
    if not DOCX_AVAILABLE:
        return "DOCX support not installed. Please use PDF or TXT."
    try:
        doc = docx.Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        return f"Error: {str(e)}"

def extract_text_from_txt(file):
    try:
        return file.getvalue().decode('utf-8')
    except:
        return file.getvalue().decode('latin-1')

# ==========================================================
# CLAUSE ANALYSIS FUNCTIONS
# ==========================================================

def analyze_contract_clauses(text):
    results = {}
    text_lower = text.lower()
    
    for clause_name, config in CLAUSE_PATTERNS.items():
        found = False
        preview = ""
        
        for pattern in config["patterns"]:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                found = True
                # Get context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                preview = text[start:end].strip()
                break
        
        results[clause_name] = {
            "found": found,
            "risk_level": config["risk"] if found else "missing",
            "description": config["description"],
            "preview": preview
        }
    
    return results

def calculate_risk_score(results):
    scores = {
        "high": 75,
        "medium": 50,
        "low": 25,
        "missing": 0
    }
    
    total_score = 0
    for clause, data in results.items():
        total_score += scores[data["risk_level"]]
    
    # Average score
    avg_score = total_score / len(results) if results else 0
    return min(100, avg_score)

# ==========================================================
# AI FUNCTIONS
# ==========================================================

def improve_contract_with_ai(contract_text):
    if not client:
        return "⚠️ AI not available. Please configure GROQ_API_KEY."
    
    try:
        prompt = f"""You are a legal expert. Analyze and improve this contract to make it more balanced and legally safer.

Contract:
{contract_text[:8000]}

Instructions:
1. Identify risky clauses (payment terms, liability limits, termination, confidentiality)
2. Rewrite these clauses to be more balanced
3. Keep all legitimate business terms
4. Maintain the contract structure

Provide the improved contract:"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def ask_chatbot(question, contract_text):
    if not client:
        return "⚠️ AI not available. Please configure GROQ_API_KEY."
    
    if not contract_text:
        return "Please upload a contract first."
    
    try:
        prompt = f"""You are a legal contract assistant. Answer questions about the contract below.

Contract:
{contract_text[:6000]}

Question: {question}

Provide a clear, helpful answer:"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================================
# EMAIL FUNCTION
# ==========================================================

def send_contract_email(recipient, subject, body, attachment_text=None):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file."
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Create HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #667eea;">📋 RegulaAI Contract Delivery</h2>
            <p>Please find your contract below.</p>
            <hr>
            <pre style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word;">{body[:5000]}</pre>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This email was sent from RegulaAI - AI-Powered Regulatory Compliance Platform.<br>
                Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        if attachment_text:
            attachment = MIMEText(attachment_text, 'plain', 'utf-8')
            attachment.add_header('Content-Disposition', 'attachment', filename='contract.txt')
            msg.attach(attachment)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
        server.quit()
        
        return True, "Email sent successfully!"
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please check SENDER_EMAIL and SENDER_PASSWORD in .env file. For Gmail, use App Password."
    except Exception as e:
        return False, f"Email error: {str(e)}"


# ==========================================================
# AUTOMATED EMAIL NOTIFICATION FUNCTIONS
# ==========================================================

def send_contract_revision_alert(recipient_email, contract_name, revision_details):
    """
    Send Contract Revision Alerts to notify contract owners when contracts require updates.
    Uses Gmail SMTP (smtp.gmail.com, port 587) with app-specific password authentication.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file."
    
    try:
        subject = f"⚠️ Contract Revision Required: {contract_name}"
        
        body = f"""REGULAAI - CONTRACT REVISION ALERT

Dear Contract Owner,

This is an automated notification from RegulaAI regarding a contract 
that requires your attention and revision.

CONTRACT DETAILS:
- Contract Name: {contract_name}
- Alert Type: Revision Required
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

REVISION DETAILS:
{revision_details}

REQUIRED ACTIONS:
1. Review the contract details above
2. Update the necessary clauses
3. Re-upload the revised contract for analysis
4. Ensure compliance with current regulations

This is an automated message from RegulaAI - AI-Powered Regulatory Compliance Platform.
"""
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())
        server.quit()
        
        return True, "Contract revision alert sent successfully!"
        
    except Exception as e:
        return False, f"Failed to send revision alert: {str(e)}"


def send_revision_confirmation(recipient_email, contract_name, improvements_made):
    """
    Send Revision Confirmations to inform users when contracts are successfully revised.
    Uses Gmail SMTP (smtp.gmail.com, port 587) with app-specific password authentication.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file."
    
    try:
        subject = f"✅ Contract Successfully Revised: {contract_name}"
        
        body = f"""REGULAAI - REVISION CONFIRMATION

Dear User,

We are pleased to inform you that your contract has been successfully 
processed and revised by RegulaAI.

CONTRACT DETAILS:
- Contract Name: {contract_name}
- Status: Successfully Revised
- Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

IMPROVEMENTS APPLIED:
{improvements_made}

Thank you for using RegulaAI - AI-Powered Regulatory Compliance Platform!
"""
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())
        server.quit()
        
        return True, "Revision confirmation sent successfully!"
        
    except Exception as e:
        return False, f"Failed to send confirmation: {str(e)}"


def send_high_risk_notification(recipient_email, contract_name, risk_details):
    """
    Send High-Risk Notifications for immediate alerts about critical compliance issues.
    Uses Gmail SMTP (smtp.gmail.com, port 587) with app-specific password authentication.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file."
    
    try:
        subject = f"🚨 URGENT: High-Risk Compliance Alert - {contract_name}"
        
        body = f"""╔══════════════════════════════════════════════════════════════════╗
║     REGULAAI - HIGH-RISK COMPLIANCE NOTIFICATION                 ║
║                    ⚠️ URGENT ACTION REQUIRED ⚠️                  ║
╚══════════════════════════════════════════════════════════════════╝

Dear User,

🚨 IMMEDIATE ATTENTION REQUIRED

A high-risk compliance issue has been detected in your contract.

CONTRACT DETAILS:
- Contract Name: {contract_name}
- Alert Level: HIGH RISK
- Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RISK DETAILS:
{risk_details}

⏰ IMMEDIATE ACTIONS REQUIRED:
1. ⚠️ DO NOT SIGN this contract until issues are resolved
2. Review the risk analysis in your RegulaAI dashboard
3. Use the AI improvement feature to enhance the contract
4. Consult with legal counsel immediately

⚠️ WARNING: Proceeding with this contract without addressing the 
above issues may result in significant legal and financial consequences.

This is an automated urgent notification from RegulaAI.
"""
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())
        server.quit()
        
        return True, "High-risk notification sent successfully!"
        
    except Exception as e:
        return False, f"Failed to send high-risk notification: {str(e)}"


# ==========================================================
# PDF GENERATION
# ==========================================================

def create_contract_pdf(contract_text, title="Contract"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, 
                                  spaceAfter=20, alignment=1)
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # Content
    content_style = ParagraphStyle('CustomContent', parent=styles['Normal'], fontSize=10,
                                   spaceAfter=12, leading=14)
    
    paragraphs = contract_text.split('\n\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), content_style))
            story.append(Spacer(1, 10))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================================
# VISUALIZATION FUNCTIONS
# ==========================================================

def create_risk_chart(results):
    risk_counts = {"High Risk": 0, "Medium Risk": 0, "Low Risk": 0, "Missing": 0}
    
    for clause, data in results.items():
        if data["risk_level"] == "high":
            risk_counts["High Risk"] += 1
        elif data["risk_level"] == "medium":
            risk_counts["Medium Risk"] += 1
        elif data["risk_level"] == "low":
            risk_counts["Low Risk"] += 1
        else:
            risk_counts["Missing"] += 1
    
    df = pd.DataFrame(list(risk_counts.items()), columns=['Category', 'Count'])
    
    colors = {'High Risk': '#ff4444', 'Medium Risk': '#ffaa00', 
              'Low Risk': '#44bb44', 'Missing': '#cccccc'}
    
    fig = px.bar(df, x='Category', y='Count', color='Category',
                 color_discrete_map=colors,
                 title="📊 Risk Distribution Across Clauses")
    
    fig.update_layout(showlegend=False, height=400)
    return fig

def create_risk_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        title = {'text': f"Overall Risk Score: {score}%"},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'steps': [
                {'range': [0, 30], 'color': '#d4edda'},
                {'range': [30, 60], 'color': '#fff3cd'},
                {'range': [60, 100], 'color': '#f8d7da'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=50, r=50, t=50, b=50))
    return fig

def create_clause_coverage_chart(results):
    found = sum(1 for r in results.values() if r["found"])
    missing = sum(1 for r in results.values() if not r["found"])
    
    fig = go.Figure(go.Pie(
        labels=['Clauses Found', 'Missing Clauses'],
        values=[found, missing],
        hole=0.4,
        marker=dict(colors=['#667eea', '#f0f0f0']
    )))
    
    fig.update_layout(title="📋 Clause Coverage", height=300)
    return fig

# ==========================================================
# MAIN APPLICATION
# ==========================================================

def main():
    # Page config
    st.set_page_config(
        page_title="RegulaAI - AI Contract Compliance",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced Custom CSS for Modern Design
    st.markdown("""
    <style>
    /* Main Theme Colors */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --success-color: #4caf50;
        --warning-color: #ff9800;
        --danger-color: #f44336;
        --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Custom Login Container */
    .login-container {
        max-width: 450px;
        margin: 60px auto;
        padding: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 25px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    }
    .login-title {
        color: white;
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .login-subtitle {
        color: rgba(255,255,255,0.9);
        text-align: center;
        margin-bottom: 30px;
        font-size: 14px;
    }
    
    /* Card Styles */
    .card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Header Styles */
    h1, h2, h3 {
        color: #1a1a2e;
        font-weight: 600;
    }
    
    /* Button Hover Effects */
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar Styles */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Expander Styles */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Custom Success/Info/Warning Boxes */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Progress Indicator */
    .spinner {
        border: 3px solid rgba(102, 126, 234, 0.1);
        border-left-color: #667eea;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Chat Message Styles */
    .chat-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 15px 15px 0 15px;
        margin: 10px 0;
    }
    .chat-ai {
        background: #f0f2f6;
        color: #1a1a2e;
        padding: 15px 20px;
        border-radius: 15px 15px 15px 0;
        margin: 10px 0;
    }
    
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Footer */
    .custom-footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check login
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Logout button in sidebar
    st.sidebar.markdown("---")
    st.sidebar.button("🚪 Logout", on_click=logout)
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.get('user_email', 'User')}")
    
    # Main title
    st.title("📋 RegulaAI - AI Contract Compliance System")
    st.caption("🤖 AI-Powered Contract Intelligence Platform")
    
    # Sidebar navigation
    st.sidebar.markdown("## 📌 Navigation")
    page = st.sidebar.radio("Go to:", [
        "📤 Upload Contract",
        "📊 Risk Analysis",
        "📈 Charts & Visualization",
        "✏️ Improve Contract",
        "📧 Email Delivery",
        "💬 AI Chat Assistant"
    ])
    
    st.markdown("---")
    
    # ==========================================================
    # UPLOAD CONTRACT PAGE
    # ==========================================================
    
    if page == "📤 Upload Contract":
        st.header("📤 Upload Contract")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Upload Methods")
            upload_method = st.radio("Choose:", ["📄 PDF File", "📝 DOCX File", "📃 TXT File", "✍️ Paste Text"],
                                     horizontal=True)
        
        with col2:
            st.subheader("Quick Stats")
            if st.session_state.contract_text:
                word_count = len(st.session_state.contract_text.split())
                char_count = len(st.session_state.contract_text)
                st.success(f"✅ Contract loaded: {word_count} words, {char_count} characters")
            else:
                st.info("ℹ️ No contract loaded yet")
        
        st.markdown("---")
        
        # File upload
        if upload_method == "📄 PDF File":
            file = st.file_uploader("Upload PDF", type=['pdf'])
            if file:
                st.session_state.contract_text = extract_text_from_pdf(file)
                st.success("✅ PDF uploaded successfully!")
                st.rerun()
                
        elif upload_method == "📝 DOCX File":
            if not DOCX_AVAILABLE:
                st.warning("⚠️ DOCX support not installed. Please use pip install python-docx")
            else:
                file = st.file_uploader("Upload DOCX", type=['docx'])
                if file:
                    st.session_state.contract_text = extract_text_from_docx(file)
                    st.success("✅ DOCX uploaded successfully!")
                    st.rerun()
                    
        elif upload_method == "📃 TXT File":
            file = st.file_uploader("Upload TXT", type=['txt'])
            if file:
                st.session_state.contract_text = extract_text_from_txt(file)
                st.success("✅ TXT uploaded successfully!")
                st.rerun()
                
        elif upload_method == "✍️ Paste Text":
            text = st.text_area("Paste contract text here:", height=300)
            if text:
                st.session_state.contract_text = text
                st.success("✅ Contract text saved!")
                st.rerun()
        
        # Show preview
        if st.session_state.contract_text:
            with st.expander("📄 Contract Preview"):
                st.text_area("", st.session_state.contract_text[:2000] + "..." if len(st.session_state.contract_text) > 2000 else st.session_state.contract_text,
                            height=300, key="preview")
    
    # ==========================================================
    # RISK ANALYSIS PAGE
    # ==========================================================
    
    elif page == "📊 Risk Analysis":
        st.header("📊 Contract Risk Analysis")
        
        if not st.session_state.contract_text:
            st.warning("⚠️ Please upload a contract first!")
            return
        
        # Analyze button
        if st.button("🔍 Analyze Contract", type="primary"):
            with st.spinner("Analyzing contract clauses..."):
                results = analyze_contract_clauses(st.session_state.contract_text)
                risk_score = calculate_risk_score(results)
                
                st.session_state.analysis_results = {
                    "results": results,
                    "risk_score": risk_score
                }
        
        # Display results
        if st.session_state.analysis_results:
            results = st.session_state.analysis_results["results"]
            risk_score = st.session_state.analysis_results["risk_score"]
            
            st.markdown("---")
            
            # Overall risk score
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Risk Score", f"{risk_score}%")
            with col2:
                found_count = sum(1 for r in results.values() if r["found"])
                st.metric("Clauses Found", f"{found_count}/{len(results)}")
            with col3:
                missing_count = sum(1 for r in results.values() if not r["found"])
                st.metric("Missing Clauses", missing_count)
            
            st.markdown("---")
            
            # Detailed clause analysis
            st.subheader("📋 Clause Analysis")
            
            for clause_name, data in results.items():
                risk = data["risk_level"]
                config = RISK_CONFIG[risk]
                
                with st.expander(f"{config['color']} {clause_name} - {config['level']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.write(f"**Status:** {'✅ Found' if data['found'] else '❌ Missing'}")
                        st.write(f"**Risk Level:** {config['color']} {config['level']}")
                        st.write(f"**Description:** {data['description']}")
                    
                    with col2:
                        if data["preview"]:
                            st.write("**Preview:**")
                            st.info(f"...{data['preview']}...")
    
    # ==========================================================
    # CHARTS PAGE
    # ==========================================================
    
    elif page == "📈 Charts & Visualization":
        st.header("📈 Risk Visualization Dashboard")
        
        if not st.session_state.analysis_results:
            st.warning("⚠️ Please analyze a contract first!")
            return
        
        results = st.session_state.analysis_results["results"]
        risk_score = st.session_state.analysis_results["risk_score"]
        
        # Risk gauge
        st.subheader("🎯 Overall Risk Assessment")
        gauge = create_risk_gauge(risk_score)
        st.plotly_chart(gauge, width='stretch')
        
        st.markdown("---")
        
        # Two columns of charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Risk Distribution")
            bar_chart = create_risk_chart(results)
            st.plotly_chart(bar_chart, width='stretch')
            
        with col2:
            st.subheader("📋 Clause Coverage")
            pie_chart = create_clause_coverage_chart(results)
            st.plotly_chart(pie_chart, width='stretch')
        
        st.markdown("---")
        
        # Risk matrix
        st.subheader("⚠️ Risk Matrix (Likelihood vs Impact)")
        
        # Create sample risk matrix data
        risk_data = []
        for clause, data in results.items():
            risk_data.append({
                "Clause": clause,
                "Severity": {"high": 3, "medium": 2, "low": 1, "missing": 0}[data["risk_level"]],
                "Found": 1 if data["found"] else 0
            })
        
        df_risk = pd.DataFrame(risk_data)
        
        if not df_risk.empty:
            fig_matrix = px.scatter(
                df_risk, x="Found", y="Severity", size="Severity", color="Clause",
                title="Clause Risk Matrix", hover_name="Clause"
            )
            fig_matrix.update_layout(
                xaxis_title="Clause Found",
                yaxis_title="Severity",
                xaxis=dict(ticktext=["Missing", "Found"], tickvals=[0, 1])
            )
            st.plotly_chart(fig_matrix, width='stretch')
    
    # ==========================================================
    # IMPROVE CONTRACT PAGE
    # ==========================================================
    
    elif page == "✏️ Improve Contract":
        st.header("✏️ AI Contract Amendment")
        
        if not st.session_state.contract_text:
            st.warning("⚠️ Please upload a contract first!")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📄 Original Contract")
            st.text_area("Original Contract Text", label_visibility="collapsed", value=st.session_state.contract_text, height=300, key="original_display")
            
        with col2:
            st.subheader("⚡ Actions")
            if st.button("🤖 Generate Improved Contract", type="primary", use_container_width=True):
                with st.spinner("🤖 AI is improving your contract..."):
                    improved = improve_contract_with_ai(st.session_state.contract_text)
                    st.session_state.improved_contract = improved
            
            if st.session_state.improved_contract:
                st.success("✅ Improved contract generated!")
                
                # Download options
                st.markdown("### 💾 Download")
                
                # Text download
                st.download_button(
                    "📥 Download as TXT",
                    st.session_state.improved_contract,
                    "improved_contract.txt",
                    "text/plain",
                    use_container_width=True
                )
                
                # PDF download
                pdf_buffer = create_contract_pdf(st.session_state.improved_contract, "Improved Contract")
                st.download_button(
                    "📥 Download as PDF",
                    pdf_buffer,
                    "improved_contract.pdf",
                    "application/pdf",
                    use_container_width=True
                )
        
        # Show improved contract
        if st.session_state.improved_contract:
            st.markdown("---")
            st.subheader("✨ Improved Contract")
            
            # Edit option
            edited = st.text_area("Edit improved contract:", st.session_state.improved_contract, height=400)
            if edited != st.session_state.improved_contract:
                st.session_state.improved_contract = edited
    
    # ==========================================================
    # EMAIL DELIVERY PAGE
    # ==========================================================
    
    elif page == "📧 Email Delivery":
        st.header("📧 Email Contract Delivery")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Email Details")
            recipient = st.text_input("Recipient Email", placeholder="recipient@example.com")
            subject = st.text_input("Subject", "Your Contract from RegulaAI")
            
            # Choose which contract to send
            contract_choice = st.radio("Contract to send:", 
                                       ["Original Contract", "Improved Contract"],
                                       horizontal=True)
            
            if contract_choice == "Original Contract":
                body_text = st.session_state.contract_text
            else:
                body_text = st.session_state.improved_contract or "No improved contract available"
        
        with col2:
            st.subheader("📤 Preview")
            if body_text:
                st.text_area("Email Body Preview:", body_text[:1000] + "..." if len(body_text) > 1000 else body_text,
                            height=200)
        
        st.markdown("---")
        
        if st.button("📧 Send Email", type="primary"):
            if not recipient:
                st.error("❌ Please enter a recipient email")
            elif "@" not in recipient:
                st.error("❌ Invalid email address")
            else:
                with st.spinner("Sending email..."):
                    attachment = body_text if contract_choice == "Improved Contract" and st.session_state.improved_contract else None
                    success, message = send_contract_email(recipient, subject, body_text, attachment)
                    
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
    
    # ==========================================================
    # AI CHAT ASSISTANT PAGE
    # ==========================================================
    
    elif page == "💬 AI Chat Assistant":
        st.header("💬 AI Contract Chat Assistant")
        
        if not st.session_state.contract_text:
            st.warning("⚠️ Please upload a contract first!")
            return
        
        # Sample questions
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "What are the main risks in this contract?",
            "Who are the parties involved?",
            "What are the payment terms?",
            "What are the termination conditions?",
            "What does the confidentiality clause say?",
            "What is the liability limitation?",
            "Are there any concerning clauses?",
            "What happens in case of breach?"
        ]
        
        cols = st.columns(4)
        for i, q in enumerate(sample_questions):
            if cols[i % 4].button(q, key=f"sample_{i}"):
                # Add to chat
                with st.spinner("Thinking..."):
                    answer = ask_chatbot(q, st.session_state.contract_text)
                    st.session_state.chat_history.append({"question": q, "answer": answer})
        
        st.markdown("---")
        
        # Chat input
        st.subheader("💬 Ask Your Question")
        
        with st.form("chat_form"):
            question = st.text_input("Ask about your contract:", placeholder="Type your question here...")
            submit = st.form_submit_button("Ask", type="primary")
        
        if submit and question:
            with st.spinner("Thinking..."):
                answer = ask_chatbot(question, st.session_state.contract_text)
                st.session_state.chat_history.append({"question": question, "answer": answer})
        
        st.markdown("---")
        
        # Chat history
        st.subheader("💭 Chat History")
        
        if st.button("🧹 Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
        
        # Display messages
        for i, msg in enumerate(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**👤 You:** {msg['question']}")
                st.markdown(f"**🤖 AI:** {msg['answer']}")
                st.markdown("---")

# Run the app
if __name__ == "__main__":
    main()

