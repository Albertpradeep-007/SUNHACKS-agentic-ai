from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from agents.graph import run_pipeline
from database import AnalysisRun, Repo, Session

router = APIRouter(tags=["analysis"])


class AnalyzeRequest(BaseModel):
    repo_id: str


@router.post("/analyze")
def start_analysis(body: AnalyzeRequest, bg: BackgroundTasks) -> dict:
    with Session() as db:
        repo = db.get(Repo, body.repo_id)
        if repo is None:
            raise HTTPException(status_code=404, detail="Repository not found")

        run_id = str(uuid.uuid4())
        run = AnalysisRun(id=run_id, repo_id=body.repo_id, status="pending", started=datetime.utcnow())
        db.add(run)
        db.commit()

    bg.add_task(run_pipeline, run_id, body.repo_id)
    return {"run_id": run_id, "status": "started"}


@router.get("/results/{run_id}")
def get_results(run_id: str) -> dict:
    with Session() as db:
        run = db.get(AnalysisRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Analysis run not found")

        return {
            "run_id": run.id,
            "repo_id": run.repo_id,
            "status": run.status,
            "raw_metrics": run.raw_metrics,
            "health_scores": run.health_scores,
            "predictions": run.predictions,
            "error": run.error,
            "started": run.started.isoformat() if run.started else None,
            "finished": run.finished.isoformat() if run.finished else None,
        }
