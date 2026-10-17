# ReviewPilot 🚀

> **Turn customer reviews into better relationships.**  
> Analyze sentiment, generate thoughtful replies, and get alerted when a customer needs immediate attention.

ReviewPilot is a production-ready, full-stack web application designed for small businesses—including cafes, restaurants, salons, gyms, and retail stores—to rapidly process batches of customer reviews, understand root cause topics, draft contextual replies, and receive instant push notifications when high-risk or urgent feedback is detected.

---

## 🌟 Key Features

1. **Batch Review Analysis**: Paste up to 20 customer reviews at once (one per line). Process them concurrently with parallel async workflows.
2. **Sentiment & Confidence Scoring**: Classifies reviews as **Positive**, **Neutral**, or **Negative** with calibrated confidence scores.
3. **Operational Topic Categorization**: Automatically groups feedback into actionable categories:
   - *Customer Service*
   - *Food & Drink Quality*
   - *Cleanliness & Hygiene*
   - *Wait Times & Speed*
   - *Pricing & Value*
   - *Ambience & Atmosphere*
   - *Facilities & Equipment*
   - *Billing & Orders*
4. **Context-Aware AI Response Drafting**: Generates customized replies matching 4 distinct tones:
   - **Friendly**: Warm, personal, appreciative.
   - **Professional**: Polished, composed, respectful.
   - **Empathetic**: Deeply validating, apologetic, solution-focused.
   - **Concise**: Direct, brief, under 2-3 sentences.
5. **Urgent Threat & Escalation Detection**: Automatically flags reviews indicating:
   - Food poisoning or health hazards
   - Physical injury or safety violations
   - Racism, harassment, or discrimination
   - Police involvement or legal action threats
   - Pest infestations (cockroaches, rodents)
   - Severe financial disputes or unauthorized charges
6. **Instant Telegram Notifications**: Automatically pushes HTML-formatted review alerts to your team's Telegram bot when urgent reviews arrive.
7. **Interactive Dashboard**:
   - Total reviews analyzed
   - Sentiment ratios (Positive, Neutral, Negative)
   - Urgent reviews count
   - Chart.js sentiment doughnut chart
   - Topic category frequency bars
   - Most common complaint callout banner
   - Recent analysis results feed with 1-click clipboard copy
   - Authentic zero-state when no data exists (no fabricated numbers)
8. **Export Capabilities**: 1-click export of analyzed feedback to **CSV** and **JSON**.
9. **Inline Reply Editing & Regeneration**: Edit replies inline before copying or regenerate individual replies with a different tone.

---

## 🏗️ Architecture & Technology Stack

- **Frontend**: Responsive Single-Page Application built with Semantic HTML5, Modular CSS3, Modern JavaScript (ES6+), and Chart.js.
- **Backend**: Python 3.11+ / 3.13 with **FastAPI** for high-performance async REST endpoints.
- **AI Engine**: **Anthropic Claude API** (Claude 3.5 Sonnet / Claude 3 Haiku) with resilient simulation fallback when API keys are not supplied.
- **Database**: Embedded SQLite database (`reviewpilot.db`) storing persistent review batches, response edits, and configuration.
- **Alert Dispatcher**: **Telegram Bot API** via HTTPX async client.
- **Deployment**: Render Web Service (`render.yaml` & `Procfile`) + background worker workflow.

```
ReviewPilot-AI/
├── backend/
│   ├── main.py                # FastAPI entry point & static file routing
│   ├── config.py              # Pydantic configuration & environment settings
│   ├── database.py            # SQLite database schema, CRUD, and analytics
│   ├── models.py              # Pydantic request/response schemas
│   ├── routers/
│   │   ├── reviews.py         # Batch analysis, reply editing, regeneration, stats
│   │   ├── settings.py        # Telegram credentials & Anthropic key management
│   │   └── export.py          # CSV & JSON report export endpoints
│   └── services/
│       ├── ai_service.py      # Claude 3.5 Sonnet client & intelligent fallback
│       ├── telegram_service.py# Telegram Bot API alert dispatcher & connection tester
│       └── workflow.py        # Parallel concurrency orchestrator & Render worker
├── frontend/
│   ├── index.html             # Landing page & SaaS dashboard interface
│   ├── css/
│   │   ├── main.css           # Design tokens, typography, sidebar, toasts
│   │   ├── landing.css        # Landing hero, preview, pricing, FAQ accordions
│   │   ├── dashboard.css      # Metric cards, charts, complaint callouts
│   │   └── analyzer.css       # Textarea, line counters, response cards
│   └── js/
│       ├── api.js             # Client API service
│       ├── app.js             # View switcher, presets, toast notifications
│       ├── dashboard.js       # Stats rendering, Chart.js, zero-state
│       ├── analyzer.js        # Input validation, batch analysis, inline edit
│       └── settings.js        # Telegram tester & credentials management
├── tests/
│   └── test_api.py            # Automated API integration test suite
├── render.yaml                # Render Web Service & Worker blueprint
├── Procfile                   # Process definition for web servers
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── .gitignore                 # Standard exclusions
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.11+ or 3.13+
- Git

### 2. Clone and Setup Environment
```bash
git clone https://github.com/your-username/ReviewPilot-AI.git
cd ReviewPilot-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your Anthropic API key and Telegram Bot credentials:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=123456789
TELEGRAM_ALERTS_ENABLED=true
BUSINESS_NAME=Urban Bistro & Cafe
BUSINESS_TYPE=Restaurant / Cafe
```
> **Note**: Even without an Anthropic API key or Telegram bot, ReviewPilot operates out-of-the-box using its built-in sentiment simulation engine!

### 4. Run the Development Server
```bash
# Windows (PowerShell):
$env:PYTHONPATH="."
.\.venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# macOS/Linux:
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
# Windows:
$env:PYTHONPATH="."
.\.venv\Scripts\python tests/test_api.py

# macOS/Linux:
PYTHONPATH=. python tests/test_api.py
```

---

## ☁️ Deployment on Render

This repository includes a native `render.yaml` configuration for 1-click Render blueprint deployments:

1. Push your repository to **GitHub**.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** > **Blueprint**.
4. Connect your `ReviewPilot-AI` repository.
5. Render will automatically detect `render.yaml` and configure:
   - **Web Service (`reviewpilot-web`)**: Runs FastAPI with Uvicorn on `$PORT`.
   - **Worker Service (`reviewpilot-workflow-worker`)**: Runs the parallel batch workflow daemon.
6. Provide your environment variables (`ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) in the Render Dashboard under **Environment Variables**.
7. Click **Apply** to deploy!

---

## 📱 Setting Up Telegram Urgent Alerts

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`, choose a name and username, and copy the **Bot Token**.
3. Search for `@userinfobot` on Telegram and send `/start` to copy your numerical **Chat ID** (or invite your bot to a business group and get the group ID).
4. In ReviewPilot, navigate to **Settings & Alerts**.
5. Paste your **Bot Token** and **Chat ID**, toggle **Enable urgent push alerts**, and click **Test Telegram Connection**.
6. You will receive an instant test ping confirming the connection.

---

## 📄 License

MIT License. Designed and engineered for small business owners and SaaS operators.
