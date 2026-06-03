📋 RegulaAI — AI-Powered Regulatory Compliance

AI-Powered Contract Intelligence Platform built with Streamlit and Groq LLM.

RegulaAI helps legal teams, businesses, and individuals analyze contracts for compliance risks, identify missing clauses, generate improved drafts, and interact with contract content through a conversational AI assistant — all in a clean, modern web interface.

🖥️ App Screenshots
LoginUpload ContractRisk AnalysisClean login with email/password authUpload PDF, DOCX, or TXT contractsAI-driven clause detection & risk scoring
Charts & VisualizationContract ImprovementAI Chat AssistantRisk gauge, distribution charts, risk matrixAI-generated improved contract draftAsk natural language questions about contracts

✨ Features

📤 Contract Upload — Supports PDF, DOCX, and TXT file formats, plus direct text paste
🔍 Risk Analysis — Detects 12 standard legal clauses (Confidentiality, Termination, Payment Terms, Liability, and more), assigns risk scores (High / Medium / Low), and flags missing clauses
📊 Charts & Visualization — Interactive risk gauge meter, risk distribution bar chart, clause coverage donut chart, and a Likelihood vs Impact risk matrix (powered by Plotly)
✏️ Contract Improvement — AI generates an improved, legally balanced version of your contract using Groq LLM
📧 Email Delivery — Send the original or improved contract directly to any recipient via email
💬 AI Chat Assistant — Ask natural language questions about your contract (e.g., "What are the payment terms?" or "Are there any concerning clauses?")
🔐 Authentication — Session-based login system with email/password validation


🗂️ Project Structure
Ai Powered Regulatory Compliance/
├── apps.py              # Main Streamlit application (all features)
├── stream.py            # Streamlit entry/config helper
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (API keys & email credentials)
└── TODO.md              # Design improvement log

⚙️ Setup & Installation
1. Clone the Repository
bashgit clone https://github.com/Sreeja-hub-code/Ai-Powered-Regulatory-Compliance.git
cd "Ai-Powered-Regulatory-Compliance"
2. Install Dependencies
bashpip install -r requirements.txt

Optional: Install python-docx for DOCX support:
bashpip install python-docx

3. Configure Environment Variables
Create a .env file in the project root:
envGROQ_API_KEY=your_groq_api_key_here
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password

GROQ_API_KEY — Get a free key at console.groq.com
SENDER_EMAIL / SENDER_PASSWORD — For Gmail, use an App Password (not your regular password)

4. Run the App
bashstreamlit run apps.py
The app will open at http://localhost:8501.

🚀 Usage Guide

Login — Enter any valid email and a password (6+ characters) to access the platform
Upload Contract — Navigate to Upload Contract, choose your file type, and upload or paste your contract text
Analyze — Go to Risk Analysis and click Analyze Contract to get a full clause breakdown and overall risk score
Visualize — Visit Charts & Visualization to explore the risk gauge, distribution charts, and risk matrix
Improve — Head to Improve Contract and click Generate Improved Contract to get an AI-enhanced version
Email — Use Email Delivery to send the original or improved contract to any recipient
Chat — Open AI Chat Assistant and ask any question about your contract


🧩 Clause Types Analyzed
ClauseRisk LevelConfidentialityMediumTerminationHighPayment TermsHighLiabilityHighIntellectual PropertyMediumDispute ResolutionMediumForce MajeureLowWarrantyMediumAssignmentLowIndemnificationHighNoticesLowEntire AgreementLow

🛠️ Tech Stack
LayerTechnologyFrontend / UIStreamlitAI / LLMGroq (llama3-8b-8192)PDF ParsingPyPDF2DOCX Parsingpython-docxChartsPlotly, MatplotlibPDF ExportReportLabEmailPython smtplib (SMTP/SSL)Environmentpython-dotenv

📦 Dependencies
streamlit
python-dotenv
PyPDF2==3.0.1
matplotlib
reportlab
groq==0.9.0
plotly
pandas
numpy
python-docx  (optional, for DOCX support)

🔑 Environment Variables Reference
VariableRequiredDescriptionGROQ_API_KEY✅ YesGroq API key for AI features (risk analysis, improvement, chat)SENDER_EMAIL✅ For emailGmail address used to send contractsSENDER_PASSWORD✅ For emailGmail App Password (not regular password)

⚠️ Notes

The login system uses session-based validation (any valid email format + 6+ char password). For production use, integrate a proper user database with hashed passwords.
AI features (risk analysis, contract improvement, chat) require a valid GROQ_API_KEY. Without it, the app will load but AI calls will fail.
Email delivery requires Gmail SMTP with App Passwords enabled (2FA must be on for your Google account).
Contract files are processed in-memory and are not stored on disk.


📄 License
This project is open source. Feel free to use, modify, and distribute.

Built with ❤️ using Streamlit + Groq
