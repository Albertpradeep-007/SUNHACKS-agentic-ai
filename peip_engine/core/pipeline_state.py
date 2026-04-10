"""
PEIP Pipeline State Object

This is the single source of truth the orchestrator holds in memory
across all 6 pipeline steps. Every agent reads a slice of it and writes
back. Without this, each agent call is blind.

Schema contract — every key and its expected type is documented below.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


# ─────────────────────────────────────────────
# Step enum — strict ordering
# ─────────────────────────────────────────────

class Step(Enum):
    IDLE     = auto()
    FETCH    = auto()   # GitHistoryAgent — PyDriller + GitHub API
    MINE     = auto()   # ComplexityAgent  — Radon CC/MI/RAW + TDI
    ANALYZE  = auto()   # RiskAgent        — signal-level classification
    SCORE    = auto()   # HealthScoreAgent — signal summary per repo
    PATCH    = auto()   # PatchAgent       — generate actual fix patches via Ollama
    PREDICT  = auto()   # BugPrediction    — run exact future crash predictions
    REPORT   = auto()   # CEOReportAgent   — business narrative
    DELIVER  = auto()   # DashboardAgent   — render to user
    DONE     = auto()
    FAILED   = auto()   # only if zero repos have ANY data


class RepoStatus(Enum):
    PENDING   = "pending"
    FETCHED   = "fetched"       # GitHistoryAgent completed
    ANALYZED  = "analyzed"      # ComplexityAgent completed
    SCORED    = "scored"        # RiskAgent completed
    PATCHED   = "patched"       # PatchAgent completed
    PREDICTED = "predicted"     # Prediction completed
    REPORTED  = "reported"      # CEOReportAgent consumed this repo's data
    SKIPPED   = "skipped"       # insufficient data — logged, pipeline continues
    FAILED    = "failed"        # agent hard-failed on this repo


# ─────────────────────────────────────────────
# Per-repo state slice
# ─────────────────────────────────────────────

@dataclass
class RepoState:
    name:   str
    status: RepoStatus            = RepoStatus.PENDING

    # Outputs written by each agent
    git_history:  dict | None     = None   # written by FETCH step
    complexity:   dict | None     = None   # written by MINE step
    risk:         dict | None     = None   # written by ANALYZE step
    health:       dict | None     = None   # written by SCORE step
    patches:      list | None     = None   # written by PATCH step
    bug_predictions: dict | None  = None   # written by PREDICT step

    # Local workspace
    local_path:   str | None      = None

    # Degraded-mode flags
    no_python_files:   bool       = False  # Radon found nothing — CC/MI skipped
    pydriller_failed:  bool       = False  # PyDriller unavailable — git signals only
    github_api_failed: bool       = False  # GitHub API rate-limited or failed

    # Per-repo warnings collected during pipeline
    warnings: list[str]           = field(default_factory=list)

    # Timing
    started_at:   str | None      = None
    completed_at: str | None      = None

    def add_warning(self, msg: str) -> None:
        self.warnings.append(f"[{self.name}] {msg}")


# ─────────────────────────────────────────────
# Global pipeline state
# ─────────────────────────────────────────────

@dataclass
class PipelineState:
    session_id:    str
    started_at:    str                      = field(default_factory=lambda: datetime.now().isoformat())

    # Session config (written by InputAgent)
    github_username:      str               = ""
    repos:                list[str]         = field(default_factory=list)
    token:                str | None        = None
    analysis_window_days: int               = 90

    # Per-repo state indexed by repo name
    repo_states:   dict[str, RepoState]    = field(default_factory=dict)

    # Current pipeline position
    current_step:  Step                    = Step.IDLE
    current_repo:  str | None             = None

    # Cross-repo outputs (written after all repos complete a step)
    ceo_report:    str | None             = None  # written by REPORT step
    delivery_done: bool                   = False

    # Pipeline-level log (append-only, never redacted)
    log: list[dict]                       = field(default_factory=list)

    # ── Computed views ──────────────────────

    def repos_with_status(self, *statuses: RepoStatus) -> list[str]:
        return [
            name for name, rs in self.repo_states.items()
            if rs.status in statuses
        ]

    @property
    def any_data_at_all(self) -> bool:
        """True if at least one repo produced any output. Gate for total failure."""
        return any(
            rs.git_history is not None or rs.complexity is not None
            for rs in self.repo_states.values()
        )

    @property
    def all_warnings(self) -> list[str]:
        pipeline_warnings = [e["message"] for e in self.log if e.get("level") == "WARN"]
        repo_warnings = []
        for rs in self.repo_states.values():
            repo_warnings.extend(rs.warnings)
        return pipeline_warnings + repo_warnings

    @property
    def summary(self) -> dict:
        return {
            "session_id":   self.session_id,
            "repos_total":  len(self.repo_states),
            "repos_ok":     len(self.repos_with_status(
                                RepoStatus.FETCHED, RepoStatus.ANALYZED,
                                RepoStatus.SCORED, RepoStatus.REPORTED)),
            "repos_skipped": len(self.repos_with_status(RepoStatus.SKIPPED)),
            "repos_failed":  len(self.repos_with_status(RepoStatus.FAILED)),
            "current_step":  self.current_step.name,
        }

    # ── Logging ─────────────────────────────

    def write_log(self, level: str, step: str, repo: str | None, message: str,
                  payload: Any = None) -> None:
        entry = {
            "ts":      datetime.now().isoformat(),
            "level":   level,       # INFO | WARN | ERROR | SKIP | TRANSITION
            "step":    step,
            "repo":    repo,
            "message": message,
        }
        if payload is not None:
            entry["payload"] = payload
        self.log.append(entry)

    def info(self,  step, repo, msg, payload=None): self.write_log("INFO",       step, repo, msg, payload)
    def warn(self,  step, repo, msg, payload=None): self.write_log("WARN",       step, repo, msg, payload)
    def error(self, step, repo, msg, payload=None): self.write_log("ERROR",      step, repo, msg, payload)
    def skip(self,  step, repo, msg, payload=None): self.write_log("SKIP",       step, repo, msg, payload)
    def transition(self, from_step, to_step, repo=None):
        self.write_log("TRANSITION", from_step, repo,
                       f"{from_step} -> {to_step}")


# ─────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────

def new_pipeline_state(session_config: dict) -> PipelineState:
    import uuid
    repos = session_config.get("repos", [])
    ps = PipelineState(
        session_id            = str(uuid.uuid4())[:8],
        github_username       = session_config.get("github_username", ""),
        repos                 = repos,
        token                 = session_config.get("token"),
        analysis_window_days  = session_config.get("analysis_window_days", 90),
    )
    for r in repos:
        ps.repo_states[r] = RepoState(name=r)
    return ps
