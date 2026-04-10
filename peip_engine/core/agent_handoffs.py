"""
PEIP Agent Handoff Format — JSON Contracts

Defines the exact schema the orchestrator builds before calling each agent,
and what it injects from PipelineState into each payload.

The orchestrator is responsible for BUILDING each payload from state.
Agents only receive slices — they never read PipelineState directly.

Import this module to build and validate handoff payloads.
"""

from datetime import datetime


# ─────────────────────────────────────────────
# HANDOFF 1: Orchestrator → GitHistoryAgent
# ─────────────────────────────────────────────

def build_fetch_payload(ps) -> dict:
    """
    Slice of PipelineState sent to GitHistoryAgent.
    GitHistoryAgent only sees what it needs — nothing else.
    """
    return {
        "github_username":      ps.github_username,
        "token":                ps.token,
        "analysis_window_days": ps.analysis_window_days,
        # Per-repo list comes from the orchestrator loop — not included here
    }


def build_fetch_repo_args(repo: str, payload: dict) -> dict:
    """
    Per-repo call arguments for GitHistoryAgent.
    repo_path is always the remote GitHub URL.
    """
    return {
        "repo_name":        repo,
        "repo_path":        f"https://github.com/{payload['github_username']}/{repo}.git",
        "window_days":      payload["analysis_window_days"],
        "token":            payload["token"],
        "github_username":  payload["github_username"],
    }


EXPECTED_GIT_HISTORY_KEYS = {
    "repo",
    "analysis_window_days",
    "pydriller_available",
    "hotspot_files",
    "single_owner_hotspot_files",
    "bus_factor_risk_files",
    "file_churn_raw",
    "file_churn_added_removed",
    "top20_churn_files",
    "top20_hunk_files",
    "avg_files_changed_together",
    "churn_trend",
    "commit_frequency_per_week",
    "deployment_frequency_per_month",
    "bug_mttr_days",
    "github_api_source",
    "coupling_flag",
}


# ─────────────────────────────────────────────
# HANDOFF 2: Orchestrator → ComplexityAgent
# ─────────────────────────────────────────────

def build_mine_payload(repo: str, ps, git_history_out: dict) -> dict:
    """
    ComplexityAgent receives git_history so it can compute TDI cross-signal.
    This is the critical injection: without churn_rate from here, TDI cannot
    combine CC + MI + churn as the formula requires.

    Orchestrator extracts the churn lookup the agent needs:
      file_churn_rate_map: {filepath: float} — pre-computed by orchestrator
      from git_history.file_churn_raw and git_history.file_churn_added_removed
    """
    # Build the churn rate map here so ComplexityAgent doesn't need to know
    # PyDriller's internal format — it just gets a clean {file: rate} dict.
    raw_churn  = git_history_out.get("file_churn_raw", {})
    added_rem  = git_history_out.get("file_churn_added_removed", {})

    churn_map: dict[str, float] = {}
    for filepath, raw_val in raw_churn.items():
        ar = added_rem.get(filepath)
        if isinstance(ar, (list, tuple)) and len(ar) == 2:
            added, removed = ar
            churn_map[filepath] = min((added + removed) / max(raw_val, 1), 1.0)
        else:
            churn_map[filepath] = 0.05  # conservative default

    return {
        "repo_name":           repo,
        "github_username":     ps.github_username,
        "token":               ps.token,
        "file_churn_rate_map": churn_map,  # ← critical injection for TDI
        "git_history":         git_history_out,
    }


EXPECTED_COMPLEXITY_KEYS = {
    "repo",
    "files",            # {filepath: {cc_grade, cc_max, mi_grade, mi_score, tdi, ...}}
    "repo_summary",     # {total_python_files, grade_distribution, pct_grade_C_or_worse, ...}
}


# ─────────────────────────────────────────────
# HANDOFF 3: Orchestrator → RiskAgent
# ─────────────────────────────────────────────

def build_analyze_payload(repo: str, git_history_out: dict,
                          complexity_out: dict | None) -> dict:
    """
    RiskAgent receives both upstream outputs.
    complexity_out may be None if no Python files found — RiskAgent handles this.
    """
    return {
        "repo_name":   repo,
        "git_history": git_history_out,
        "complexity":  complexity_out,   # may be None — RiskAgent handles
    }


EXPECTED_RISK_KEYS = {
    "repo",
    "repo_classification",  # CRITICAL | AT RISK | STABLE | HEALTHY | UNKNOWN
    "primary_signal",
    "total_components",
    "critical_count",
    "at_risk_count",
    "components",           # [{file, classification, signals_triggered, ...}]
    "methodology_note",
}


# ─────────────────────────────────────────────
# HANDOFF 4: Orchestrator → CEOReportAgent
# ─────────────────────────────────────────────

def build_report_payload(ps) -> dict:
    """
    CEOReportAgent receives ALL repo outputs collected in PipelineState.
    Only repos that reached SCORED or ANALYZED status are included.
    """
    from pipeline_state import RepoStatus

    risk_output:       dict = {}
    complexity_output: dict = {}
    git_history_output: dict = {}

    for repo, rs in ps.repo_states.items():
        if rs.status in (RepoStatus.SKIPPED, RepoStatus.FAILED):
            continue  # don't include failed repos in CEO report
        if rs.risk:
            risk_output[repo] = rs.risk
        if rs.complexity:
            complexity_output[repo] = rs.complexity
        if rs.git_history:
            git_history_output[repo] = rs.git_history

    return {
        "risk_output":        risk_output,
        "complexity_output":  complexity_output,
        "git_history_output": git_history_output,
    }


# ─────────────────────────────────────────────
# HANDOFF 5: Orchestrator → DashboardAgent
# ─────────────────────────────────────────────

def build_deliver_payload(ps, ceo_report: str | None) -> dict:
    """
    DashboardAgent receives the final unified output dict.
    This is the payload written to peip_pipeline_output.json.
    """
    from pipeline_state import RepoStatus

    repos_analyzed = [
        r for r, rs in ps.repo_states.items()
        if rs.status not in (RepoStatus.SKIPPED, RepoStatus.FAILED, RepoStatus.PENDING)
    ]
    repos_skipped = [
        r for r, rs in ps.repo_states.items()
        if rs.status == RepoStatus.SKIPPED
    ]
    repos_failed = [
        r for r, rs in ps.repo_states.items()
        if rs.status == RepoStatus.FAILED
    ]

    return {
        "session_id":         ps.session_id,
        "generated_at":       datetime.now().isoformat(),
        "repos_analyzed":     repos_analyzed,
        "repos_skipped":      repos_skipped,
        "repos_failed":       repos_failed,
        "git_history":        {r: rs.git_history  for r, rs in ps.repo_states.items() if rs.git_history},
        "complexity":         {r: rs.complexity   for r, rs in ps.repo_states.items() if rs.complexity},
        "risk_flags":         {r: rs.risk         for r, rs in ps.repo_states.items() if rs.risk},
        "ceo_report":         ceo_report,
        "patches":            {r: rs.patches      for r, rs in ps.repo_states.items() if rs.patches},
        "bug_predictions":    {r: rs.bug_predictions for r, rs in ps.repo_states.items() if rs.bug_predictions},
        "pipeline_warnings":  ps.all_warnings,
        "pipeline_log":       ps.log,
    }


# ─────────────────────────────────────────────
# Validation helpers
# ─────────────────────────────────────────────

def validate_agent_output(output: dict | None, expected_keys: set,
                           agent_name: str, repo: str) -> list[str]:
    """
    Check agent output has required top-level keys.
    Returns list of missing key warnings (empty = valid).
    """
    if output is None:
        return [f"{agent_name} returned None for {repo}"]
    missing = expected_keys - set(output.keys())
    if missing:
        return [f"{agent_name} output missing keys for {repo}: {missing}"]
    return []
