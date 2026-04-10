<div align="center">

# 🧠 PEIP — Predictive Engineering Intelligence Platform

### Autonomous Multi-Agent AI System for Software Risk Prediction & Code Health Analysis

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-Groq-orange)](https://www.langchain.com/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> **Built for SUNHACKS** — AI-powered GitHub repository health analysis with a multi-agent LangGraph pipeline running on Groq (free tier). Mines repo history, scores code health, predicts near-term risk, and generates executive PDF reports.

</div>

---

## 🏆 SUNHACKS Team

<div align="center">

| | Details |
|:---|:---|
| 🏷️ **Team Name** | Agentic |
| 🔢 **Team Code** | `46CD8` |
| 👥 **Members** | Tummala Pradeep · Chaitanya · Shivaram · Akshay · Shibu |

</div>

---

## 🏗️ Architecture

```
GitHub Repo URL
      │
      ▼
┌─────────────────────────────────────────────────┐
│              LangGraph Agent Pipeline            │
│                                                  │
│  [Miner] → [Scorer] → [Predictor] → [Reporter] │
└─────────────────────────────────────────────────┘
      │
      ▼
FastAPI Backend (port 8000)
      │
      ▼
React + Vite Frontend (port 5173)
```

| Layer       | Tech                                    |
|-------------|------------------------------------------|
| Frontend    | React 18, Vite, custom CSS              |
| Backend     | FastAPI, SQLAlchemy, Uvicorn            |
| AI Pipeline | LangGraph, Groq (llama-3.1-8b-instant) |
| PDF Reports | WeasyPrint / ReportLab fallback         |
| Deployment  | Docker Compose, Render                  |

---

## 📁 Project Layout

```
PEIP/
├── backend/
│   ├── agents/           # LangGraph agent nodes
│   │   ├── miner.py      # Mines GitHub commit history
│   │   ├── scorer.py     # Scores code health metrics
│   │   ├── predictor.py  # Predicts near-term risk
│   │   └── reporter.py   # Generates executive report
│   ├── routers/          # FastAPI route handlers
│   │   ├── repos.py      # Repo management endpoints
│   │   ├── analysis.py   # Analysis trigger & status
│   │   └── report.py     # Report download endpoints
│   ├── services/         # External service wrappers
│   │   ├── github.py     # GitHub API client
│   │   ├── llm_client.py # Groq / OpenAI LLM client
│   │   └── pdf_renderer.py
│   ├── templates/        # Jinja2 HTML report template
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Environment config
│   ├── database.py       # SQLAlchemy models & DB init
│   ├── requirements.txt
│   ├── .env.example      # ← copy to .env and fill in
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/        # Connect, Dashboard, Report
│   │   ├── components/   # CostCard, HealthHeatmap, RiskTable
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── styles.css
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── Dockerfile
├── docs/
│   ├── DEPLOYMENT.md
│   └── MODULAR_WORKPACKAGES.md
├── scripts/
│   ├── start-dev.ps1     # Windows quick-start (dev)
│   └── start-prod.ps1    # Windows quick-start (prod)
├── docker-compose.yml
├── docker-compose.dev.yml
├── render.yaml
└── .env.example
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A free [Groq API key](https://console.groq.com)
- A GitHub personal access token (for private repos / higher rate limits)

---

### 1. Backend Setup

```bash
# Clone the repo
git clone https://github.com/Albertpradeep-007/SUNHACKS-agentic-ai.git
cd SUNHACKS-agentic-ai

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
copy backend\.env.example backend\.env
# Edit backend/.env and fill in your keys

# Start backend
cd backend
python -m uvicorn main:app --reload --port 8000
```

Backend API docs available at: **http://localhost:8000/docs**

---

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

### 3. One-Command Docker (Recommended for demos)

```bash
# Copy and fill in env
copy backend\.env.example backend\.env

# Build and run all services
docker compose up -d --build

# Or for hot-reload dev containers
docker compose -f docker-compose.dev.yml up --build
```

| Service  | URL                          |
|----------|-------------------------------|
| Frontend | http://localhost:5173         |
| Backend  | http://localhost:8000         |
| API Docs | http://localhost:8000/docs    |

PowerShell shortcuts:
```powershell
.\scripts\start-prod.ps1   # production
.\scripts\start-dev.ps1    # development (hot reload)
```

---

## ⚙️ Environment Variables

Copy `backend/.env.example` → `backend/.env` and fill in:

```env
# LLM — Groq is free, use it first
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# GitHub token (fine-grained PAT, read-only)
GITHUB_TOKEN=your_github_token_here

# OpenAI (optional fallback)
OPENAI_API_KEY=
```

### Getting a GitHub Token

1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click **Generate new token**
3. Set repository access to repos you want to scan
4. Required permissions: **Contents: Read-only**, **Metadata: Read-only**
5. Copy token → paste into `backend/.env` as `GITHUB_TOKEN`

---

## 🔌 API Endpoints

| Method | Endpoint              | Description                       |
|--------|-----------------------|-----------------------------------|
| GET    | `/health`             | Health check                      |
| POST   | `/repos`              | Register a GitHub repo for scan   |
| POST   | `/analyze`            | Trigger analysis pipeline         |
| GET    | `/results/{run_id}`   | Fetch analysis results            |
| GET    | `/report/{run_id}`    | Download PDF report               |
| GET    | `/report/{run_id}/html` | HTML report fallback            |

---

## 🤖 Agent Pipeline

| Agent       | What it does                                                          |
|-------------|-----------------------------------------------------------------------|
| **Miner**   | Clones repo, mines commit history, extracts churn & contributor stats |
| **Scorer**  | Runs Radon for complexity, scores code health (0–100)                 |
| **Predictor** | Uses LLM to predict risk hotspots for the next 30 days             |
| **Reporter** | Generates a formatted executive PDF/HTML report                     |

---

## 📄 PDF Report Generation

Uses **WeasyPrint** with native library support. Fallback to **ReportLab** (pure Python) when native libs are unavailable.

| OS      | Setup                                                              |
|---------|--------------------------------------------------------------------|
| Windows | Install [GTK runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer), add GTK `bin/` to PATH |
| Linux   | `apt install libpango-1.0-0 libcairo2`                            |
| macOS   | `brew install pango`                                               |

If native libraries are missing, the system automatically falls back to ReportLab — no action needed.

---

## ☁️ Free Deployment (Render)

See [`render.yaml`](./render.yaml) and [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md) for full instructions.

Render gives you:
- Free backend web service (FastAPI)
- Free static frontend hosting (Vite build)

---

## 👥 Team Collaboration

If splitting work across teammates, see [`docs/MODULAR_WORKPACKAGES.md`](./docs/MODULAR_WORKPACKAGES.md) to avoid interface breakage.

---

## 📜 License

MIT — free to use, modify, and distribute.

---

<div align="center">

**Built with ❤️ for SUNHACKS by Team Agentic (`46CD8`)**

*Predictive Engineering Intelligence — Because the best bug fix is the one you never have to make.*

| Tummala Pradeep | Chaitanya | Shivaram | Akshay | Shibu |
|:---:|:---:|:---:|:---:|:---:|
| 👨‍💻 | 👨‍💻 | 👨‍💻 | 👨‍💻 | 👨‍💻 |

</div>
