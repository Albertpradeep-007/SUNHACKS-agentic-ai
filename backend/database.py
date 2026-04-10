from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, JSON, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Repo(Base):
    __tablename__ = "repos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    token = Column(String, nullable=True)
    created = Column(DateTime, default=datetime.utcnow, nullable=False)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_id = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    started = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished = Column(DateTime, nullable=True)
    raw_metrics = Column(JSON, nullable=True)
    health_scores = Column(JSON, nullable=True)
    predictions = Column(JSON, nullable=True)
    report_md = Column(Text, nullable=True)
    report_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def mark_interrupted_runs() -> int:
    """Mark non-terminal runs as errored after process restart."""
    count = 0
    with Session() as db:
        open_runs = db.scalars(select(AnalysisRun).where(AnalysisRun.status.notin_(["done", "error"]))).all()
        for run in open_runs:
            run.status = "error"
            run.error = (run.error or "") + " | Analysis interrupted by backend restart."
            run.finished = datetime.utcnow()
            count += 1
        if count:
            db.commit()
    return count
