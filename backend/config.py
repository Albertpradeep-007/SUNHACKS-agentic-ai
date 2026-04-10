from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _split_csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return values or ["*"]


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/peip.db")
    clone_dir: str = os.getenv("CLONE_DIR", "./data/cloned_repos")
    clone_depth: int = int(os.getenv("CLONE_DEPTH", "1500"))
    clone_timeout_seconds: int = int(os.getenv("CLONE_TIMEOUT_SECONDS", "1800"))
    clone_no_checkout: bool = _bool_env("CLONE_NO_CHECKOUT", True)
    report_output_dir: str = os.getenv("REPORT_OUTPUT_DIR", "./data/reports")
    max_commits_per_window: int = int(os.getenv("MAX_COMMITS_PER_WINDOW", "3000"))
    max_files_per_commit: int = int(os.getenv("MAX_FILES_PER_COMMIT", "250"))
    max_mined_modules: int = int(os.getenv("MAX_MINED_MODULES", "800"))
    cors_origins: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", _split_csv_env("CORS_ORIGINS", "*"))


def prepare_runtime_paths() -> None:
    Path(settings.clone_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.report_output_dir).mkdir(parents=True, exist_ok=True)

    if settings.database_url.startswith("sqlite:///"):
        target = settings.database_url.replace("sqlite:///", "", 1)
        if target != ":memory:":
            db_parent = Path(target).parent
            if str(db_parent) and str(db_parent) != ".":
                db_parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
