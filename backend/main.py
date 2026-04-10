from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import prepare_runtime_paths, settings
from database import init_db, mark_interrupted_runs
from routers import analysis, report, repos

app = FastAPI(title="PEIP API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    prepare_runtime_paths()
    init_db()
    mark_interrupted_runs()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(repos.router)
app.include_router(analysis.router)
app.include_router(report.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
