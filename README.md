# CVSpark - Resume Analyzer & ATS Optimizer

CVSpark is a professional, production-ready Resume Analyzer Web Application built using Python Flask, SQLite, and Bootstrap 5. It extracts content from resumes (PDF & DOCX formats) to evaluate ATS compatibility score contributions, maps skills from a detailed technical taxonomy, detects key-term overlaps, flags formatting layouts, and uses free LLM API providers (Gemini, OpenRouter, Groq) to deliver summaries, strengths/weaknesses audits, and improvement suggestions.

---

## Features

- **Document Text Extractors:** Parses text structures from both PDF (using `pdfplumber` with `pypdf` fallbacks) and Word documents (`.docx` paragraph and table cells).
- **ATS Scoring Engine:** Evaluates CV content based on deterministic segment criteria (Contact Info, Experience metrics, Education, Technical Skills count, formatting layouts).
- **Job Map Audits:** Compares resume skills against target job description requirements to extract keyword coverage ratios, missing technical skills, and match percentages.
- **Dynamic AI Providers:** Supports multiple free LLM endpoints (Google Gemini, OpenRouter, and Groq). API keys can be entered directly and saved locally via the web interface.
- **Resilient Fallbacks:** Runs local heuristic models if no API keys are configured, ensuring the application remains fully functional out-of-the-box.
- **Interactive Visualizations:** Renders visual dashboards containing progress gauges and category comparison bar charts using Chart.js.
- **Professional PDF Export:** Dynamically builds a styled PDF report using the ReportLab layout engine.
- **Archives / History Log:** Track previous scans, search by filename, filter by score/date, and safely delete archive rows.
- **Dark & Light Mode:** Seamless transition with state persistence saved directly in `localStorage`.

---

## Directory Structure

```text
resume-analyzer/
│
├── app.py                      # Flask Application Configuration & Controller Routes
├── requirements.txt            # Python Dependencies
├── .env.example                # Template for Environment Configuration
├── .env                        # Active Environment File (Git Ignored)
├── database.db                 # SQLite database (auto-generated on app launch)
│
├── models/
│   ├── __init__.py             # Models package initialization
│   └── models.py               # SQLAlchemy Database Schemas (Resume, Analysis, Setting)
│
├── services/
│   ├── __init__.py             # Services package initialization
│   ├── parser.py               # PDF and DOCX text extraction utilities
│   ├── ats.py                  # Heuristic scoring engine & skill matching taxonomy
│   ├── ai_analysis.py          # AI integration API (Gemini, OpenRouter, Groq)
│   └── report_generator.py     # Styled PDF report generator using ReportLab
│
├── static/
│   ├── css/
│   │   └── style.css           # Premium styling sheet supporting light and dark themes
│   ├── js/
│   │   └── main.js            # Frontend interactions, drag-and-drop, and API testing
│   └── uploads/                # Directory storing secure uploaded documents (Auto-created)
│
├── templates/
│   ├── base.html               # Shared layout wrapper with navbar & theme toggler
│   ├── index.html              # Home landing page with statistics and recent items feed
│   ├── upload.html             # Resume drag-and-drop & Job Description mapping forms
│   ├── dashboard.html          # Interative report widgets, skills grids, and Chart.js script
│   └── settings.html           # API Keys management, model configurations, & test utilities
│
└── test_app.py                 # Comprehensive unit & integration testing suite
```

---

## Local Setup & Installation

### 1. Clone or Move to Project Directory
Ensure you are in the workspace folder:
```bash
cd "c:\Users\Naren J\resume analysier"
```

### 2. Set Up a Virtual Environment (Recommended)
Create and activate a Python virtual environment to isolate package configurations:
```powershell
# Create environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on Windows (CMD)
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies
Run `pip` to install all required libraries:
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Configs
Copy `.env.example` to `.env` (already created during setup) and edit credentials as desired:
```bash
cp .env.example .env
```

### 5. Initialize & Run Web Server
Run the Flask server:
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser to access the web application.

---

## Execution of Verification Tests

Run the custom test suite using Python's standard `unittest` framework:
```bash
python -m unittest test_app.py
```
This suite verifies text formatting cleanup, skill matching regex patterns, SQLite record commits, cascading relationships, and Flask endpoint structures.

---

## Configuring Free AI Credentials

To unlock full AI reviews, visit the **API Settings** tab on the web application:

1.  **Google Gemini (Recommended):**
    *   Visit [Google AI Studio](https://aistudio.google.com/) to obtain a free API key.
    *   Select **Gemini** as the active provider, enter the key, select `gemini-1.5-flash`, and click **Test Connection** before saving.
2.  **OpenRouter:**
    *   Create a free account and generate an API key at [OpenRouter Console](https://openrouter.ai/keys).
    *   Supports free models such as `google/gemini-2.5-flash:free`, `meta-llama/llama-3.3-70b-instruct:free`, or `deepseek/deepseek-chat:free`.
3.  **Groq:**
    *   Obtain a free API key at the [Groq Console](https://console.groq.com/keys).
    *   Select **Groq** as the active provider and map models like `llama-3.3-70b-versatile`.
