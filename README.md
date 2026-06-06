# 📋 RegulaAI — AI-Powered Regulatory Compliance

AI-Powered Contract Intelligence Platform built with Streamlit and Groq LLM.

RegulaAI helps legal teams, businesses, and individuals analyze contracts for compliance risks, identify missing clauses, generate improved drafts, and interact with contract content through a conversational AI assistant.

## ✨ Features

* 📤 Contract Upload (PDF, DOCX, TXT)
* 🔍 Risk Analysis with clause detection
* 📊 Interactive Charts & Visualizations
* ✏️ AI-Powered Contract Improvement
* 📧 Email Delivery
* 💬 AI Chat Assistant
* 🔐 Authentication System

## 🗂️ Project Structure

```text
Ai-Powered-Regulatory-Compliance/
├── apps.py
├── stream.py
├── requirements.txt
├── .env
└── TODO.md
```

## ⚙️ Setup & Installation

### Clone Repository

```bash
git clone https://github.com/Sreeja-hub-code/Ai-Powered-Regulatory-Compliance.git
cd Ai-Powered-Regulatory-Compliance
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
```

### Run Application

```bash
streamlit run apps.py
```

## 🧩 Clause Types Analyzed

* Confidentiality
* Termination
* Payment Terms
* Liability
* Intellectual Property
* Dispute Resolution
* Force Majeure
* Warranty
* Assignment
* Indemnification
* Notices
* Entire Agreement

## 🛠️ Tech Stack

* Streamlit
* Groq (Llama3-8B-8192)
* PyPDF2
* python-docx
* Plotly
* Matplotlib
* ReportLab
* Pandas
* NumPy

## 📄 License

Open Source Project.

Built with using Streamlit + Groq.
