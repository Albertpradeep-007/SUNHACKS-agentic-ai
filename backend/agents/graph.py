from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from config import settings
from database import AnalysisRun, Repo, Session
from agents.miner import mine_repo
from agents.predictor import predict_risks
from agents.reporter import generate_report
from agents.scorer import compute_health_scores
from services.github import clone_or_pull
from services.pdf_renderer import render_pdf


class PipelineState(TypedDict, total=False):
    run_id: str
    repo_id: str
    repo_path: str
    raw_metrics: list[dict]
    health_scores: list[dict]
    predictions: list[dict]
    report_md: str


def _update_run_status(run_id: str, status: str, error: str | None = None) -> None:
    with Session() as db:
        run = db.get(AnalysisRun, run_id)
        if run is None:
            return
        run.status = status
        if error is not None:
            run.error = error
        db.commit()


def node_mine(state: PipelineState) -> PipelineState:
    with Session() as db:
        repo = db.get(Repo, state["repo_id"])
        if repo is None:
            raise ValueError("Repository not found")

    _update_run_status(state["run_id"], "cloning")
    repo_path = clone_or_pull(
        repo.url,
        repo.token or settings.github_token,
        settings.clone_dir,
        clone_depth=settings.clone_depth,
        timeout_seconds=settings.clone_timeout_seconds,
        no_checkout=settings.clone_no_checkout,
    )

    _update_run_status(state["run_id"], "mining")
    raw_metrics = mine_repo(repo_path)
    state.update({"repo_path": repo_path, "raw_metrics": raw_metrics})
    return state


def node_score(state: PipelineState) -> PipelineState:
    _update_run_status(state["run_id"], "scoring")
    scores = compute_health_scores(state.get("raw_metrics", []), state["repo_path"])
    state["health_scores"] = scores
    return state


def node_predict(state: PipelineState) -> PipelineState:
    _update_run_status(state["run_id"], "predicting")
    state["predictions"] = predict_risks(state.get("health_scores", []))
    return state


def node_report(state: PipelineState) -> PipelineState:
    _update_run_status(state["run_id"], "reporting")
    with Session() as db:
        repo = db.get(Repo, state["repo_id"])
        if repo is None:
            raise ValueError("Repository not found")

    report_md = generate_report(repo.name, state.get("predictions", []), state.get("health_scores", []))
    state["report_md"] = report_md
    return state


workflow = StateGraph(PipelineState)
workflow.add_node("mine", node_mine)
workflow.add_node("score", node_score)
workflow.add_node("predict", node_predict)
workflow.add_node("report", node_report)
workflow.set_entry_point("mine")
workflow.add_edge("mine", "score")
workflow.add_edge("score", "predict")
workflow.add_edge("predict", "report")
workflow.add_edge("report", END)
pipeline = workflow.compile()


def run_pipeline(run_id: str, repo_id: str) -> None:
    with Session() as db:
        run = db.get(AnalysisRun, run_id)
        if run is None:
            raise ValueError("Analysis run not found")
        run.status = "running"
        run.error = None
        db.commit()

    result: dict = {}
    try:
        result = pipeline.invoke({"run_id": run_id, "repo_id": repo_id})

        report_dir = Path(settings.report_output_dir)
        pdf_path = None
        pdf_warning = None
        try:
            pdf_path = render_pdf(result.get("report_md", ""), str(report_dir / f"{run_id}.pdf"), title="PEIP CEO Risk Report")
        except Exception as exc:
            pdf_warning = str(exc)

        with Session() as db:
            run = db.get(AnalysisRun, run_id)
            if run is None:
                raise ValueError("Analysis run not found")
            run.raw_metrics = result.get("raw_metrics", [])
            run.health_scores = result.get("health_scores", [])
            run.predictions = result.get("predictions", [])
            run.report_md = result.get("report_md", "")
            run.report_path = pdf_path
            run.status = "done"
            run.error = pdf_warning
            run.finished = datetime.utcnow()
            db.commit()
    except Exception as exc:
        with Session() as db:
            run = db.get(AnalysisRun, run_id)
            if run is not None:
                run.raw_metrics = result.get("raw_metrics") if isinstance(result, dict) else None
                run.health_scores = result.get("health_scores") if isinstance(result, dict) else None
                run.predictions = result.get("predictions") if isinstance(result, dict) else None
                run.report_md = result.get("report_md") if isinstance(result, dict) else None
                run.status = "error"
                run.error = str(exc)
                run.finished = datetime.utcnow()
                db.commit()
        raise
