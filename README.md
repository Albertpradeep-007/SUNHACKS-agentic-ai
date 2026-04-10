# PEIP - Predictive Engineering Impact Platform

PEIP mines repository history, scores code health, predicts near-term risk, and generates an executive report.
It is configured for free-tier usage first (Groq by default for LLM calls).

## Project layout

- backend: FastAPI API, SQLAlchemy models, agent pipeline
- frontend: React + Vite dashboard
- docs: deployment and modular task ownership

## Backend setup (recommended)

1. Create and activate a virtual environment.
2. Install dependencies:

   python -m pip install -r backend/requirements.txt

3. Copy env template:

   copy backend\.env.example backend\.env

4. Start backend:

   cd backend
   python -m uvicorn main:app --reload --port 8000

Groq-first configuration (default):

- LLM_PROVIDER=groq
- GROQ_API_KEY=your free Groq API key
- GROQ_MODEL=llama-3.1-8b-instant

OpenAI is optional fallback only.

## Frontend setup

1. Install dependencies:

   cd frontend
   npm install

2. Start dev server:

   npm run dev

Frontend runs on http://localhost:5173 and calls backend at http://localhost:8000 by default.

## One-command Docker deployment

1. Create backend env:

   copy backend\.env.example backend\.env

2. Build and run:

   docker compose up -d --build

3. Open app:

   - Frontend: http://localhost:5173
   - Backend docs: http://localhost:8000/docs

4. Stop:

   docker compose down

PowerShell one-command launcher:

scripts\start-prod.ps1

For local hot-reload containers:

docker compose -f docker-compose.dev.yml up --build

PowerShell one-command launcher:

scripts\start-dev.ps1

## API smoke test

- Health endpoint: GET /health
- Add repo: POST /repos
- Start analysis: POST /analyze
- Fetch results: GET /results/{run_id}
- HTML report fallback: GET /report/{run_id}/html

## PDF generation note

Report PDF generation uses WeasyPrint and native libraries.

- Windows: install GTK runtime that provides gobject/pango/cairo, then add GTK bin folder to PATH.
- Linux: install libpango-1.0-0 and libcairo2.
- macOS: install pango.

If native libraries are missing, report generation falls back to a pure-Python PDF renderer (ReportLab), including on Windows.

## GitHub token setup

Use a fine-grained personal access token with at least read-only repository access.

1. GitHub profile -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens.
2. Click Generate new token.
3. Set repository access to the repos you want to scan.
4. Set permissions:
   - Contents: Read-only
   - Metadata: Read-only
5. Copy token once and place it in backend/.env as GITHUB_TOKEN.

For private repos, this token is required. For public repos, you can run without it but may hit API limits.

## Free deployment recommendation

Use Render for free-tier demos. It is more straightforward for a backend web service plus static frontend.
See render.yaml and docs/DEPLOYMENT.md.

## Modular teamwork

If you are splitting work across teammates, use docs/MODULAR_WORKPACKAGES.md to avoid interface breakage.
For deployment details, see docs/DEPLOYMENT.md.
