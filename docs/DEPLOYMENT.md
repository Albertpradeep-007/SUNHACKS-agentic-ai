# Deployment Guide

## 1) Required secrets and configuration

Create backend/.env from backend/.env.example and set:

- OPENAI_API_KEY
- GITHUB_TOKEN
- GROQ_API_KEY (recommended for free tier)
- DATABASE_URL (default sqlite works)
- CLONE_DIR
- REPORT_OUTPUT_DIR

Optional root .env values for ports and frontend API base are in .env.example.
Default LLM path is Groq (LLM_PROVIDER=groq).

## 2) Instant production-like run with Docker

Build and run:

docker compose up -d --build

Or use:

scripts\start-prod.ps1

Open:

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

Stop:

docker compose down

## 3) Development mode containers

Use live-reload dev stack:

docker compose -f docker-compose.dev.yml up --build

Or use:

scripts\start-dev.ps1

## 4) Non-container local run

Backend:

cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

Frontend:

cd frontend
npm install
npm run dev

## 5) Windows PDF support

If WeasyPrint fails on Windows, install GTK runtime that includes gobject, pango, and cairo.
PEIP now includes a ReportLab fallback, so PDF generation still works for free-tier setups without GTK.

## 6) Render free-tier deployment (recommended)

Use the render.yaml blueprint at repository root.

Steps:

1. Push this repo to GitHub.
2. In Render, create a Blueprint and point it to this repo.
3. Fill GROQ_API_KEY and GITHUB_TOKEN in Render env vars.
4. Deploy both services:
	- peip-backend (web service)
	- peip-frontend (static site)

Set frontend VITE_API_BASE to your backend public URL if needed.

