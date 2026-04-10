# PEIP Modular Work Packages

Use this split to assign tasks without breaking shared contracts.

## Package A - Ingestion + Metrics

- Ownership scope: backend services and metric extraction.
- Primary files:
  - backend/services/github.py
  - backend/agents/miner.py
  - backend/services/radon_runner.py
- Contract output shape:
  - module
  - commit_count
  - bug_fix_count
  - churn
  - authors
  - last_modified

## Package B - Scoring + Prediction

- Ownership scope: health scoring and risk prediction logic.
- Primary files:
  - backend/agents/scorer.py
  - backend/agents/predictor.py
- Contract output shape:
  - score
  - tier
  - complexity
  - bug_density
  - projected_score_90d
  - risk_probability

## Package C - Report Generation

- Ownership scope: narrative generation, markdown/html/pdf report handling.
- Primary files:
  - backend/agents/reporter.py
  - backend/services/pdf_renderer.py
  - backend/templates/report.html
  - backend/routers/report.py

## Package D - API + Orchestration

- Ownership scope: endpoints, run lifecycle, graph wiring.
- Primary files:
  - backend/main.py
  - backend/agents/graph.py
  - backend/routers/repos.py
  - backend/routers/analysis.py
  - backend/database.py

## Package E - Frontend Experience

- Ownership scope: user flows, UI, and API integrations.
- Primary files:
  - frontend/src/App.jsx
  - frontend/src/api.js
  - frontend/src/pages/Connect.jsx
  - frontend/src/pages/Dashboard.jsx
  - frontend/src/pages/Report.jsx
  - frontend/src/components/*

## Shared Rules

- Do not rename API paths without coordinating with frontend package owner.
- Do not change JSON key names without updating graph and frontend consumers.
- Keep fallback behavior when PDF generation is unavailable.
- Keep DATABASE_URL, CLONE_DIR, and REPORT_OUTPUT_DIR environment driven.
