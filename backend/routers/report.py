from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
import markdown

from database import AnalysisRun, Session

router = APIRouter(tags=["report"])


@router.get("/report/{run_id}/pdf")
def download_pdf(run_id: str) -> FileResponse:
    with Session() as db:
        run = db.get(AnalysisRun, run_id)
        if run is None or not run.report_path:
            raise HTTPException(status_code=404, detail="Report not ready")
        return FileResponse(
            run.report_path,
            media_type="application/pdf",
            filename=f"peip_report_{run_id[:8]}.pdf",
        )


@router.get("/report/{run_id}/markdown")
def get_markdown(run_id: str) -> PlainTextResponse:
    with Session() as db:
        run = db.get(AnalysisRun, run_id)
        if run is None or not run.report_md:
            raise HTTPException(status_code=404, detail="Report not ready")
        return PlainTextResponse(run.report_md)


@router.get("/report/{run_id}/html")
def get_html(run_id: str) -> HTMLResponse:
    with Session() as db:
        run = db.get(AnalysisRun, run_id)
        if run is None or not run.report_md:
            raise HTTPException(status_code=404, detail="Report not ready")
        html_body = markdown.markdown(run.report_md, extensions=["tables"])
        html = (
            "<html><head><meta charset='UTF-8'><title>PEIP Report</title></head>"
            "<body style='font-family:Arial,sans-serif;padding:24px;line-height:1.5;'>"
            f"{html_body}</body></html>"
        )
        return HTMLResponse(html)
