"""
PEIP Failure Handler — Decision Table

11 failure scenarios. Each one has:
  - condition: what went wrong
  - action: what the orchestrator does
  - state_transition: what state to move the repo to
  - user_message: what to display
  - pipeline_continues: always True except one scenario

THE ONE STOP CONDITION:
  Scenario 11 — ALL repos returned zero data.
  Every other failure degrades gracefully to partial output.
"""

from pipeline_state import PipelineState, RepoState, RepoStatus

# ─────────────────────────────────────────────
# Failure scenario definitions
# ─────────────────────────────────────────────

SCENARIOS = {

    # ── FETCH step failures ──────────────────

    1: {
        "name":        "repo_not_found",
        "trigger":     "GitHub 404 / repo does not exist",
        "action":      "skip_repo",
        "transition":  RepoStatus.SKIPPED,
        "continues":   True,
        "user_msg":    "Repo '{repo}' not found on GitHub. Skipping — analysis continues for remaining repos.",
    },
    2: {
        "name":        "auth_failure",
        "trigger":     "GitHub 401 / 403 — token invalid or missing scope",
        "action":      "retry_without_token",
        "transition":  RepoStatus.PENDING,   # retry
        "continues":   True,
        "user_msg":    "Auth failed for '{repo}'. Retrying without token (public data only). Private repos will be skipped.",
    },
    3: {
        "name":        "rate_limited",
        "trigger":     "GitHub 403 RateLimitExceededException",
        "action":      "use_cached_or_skip",
        "transition":  RepoStatus.SKIPPED,
        "continues":   True,
        "user_msg":    "GitHub API rate limit hit during '{repo}'. Using cached data if available, otherwise skipping.",
    },
    4: {
        "name":        "pydriller_unavailable",
        "trigger":     "ImportError on pydriller or subprocess timeout > 5 min",
        "action":      "github_api_fallback",
        "transition":  RepoStatus.FETCHED,   # partial — continues with API data only
        "continues":   True,
        "user_msg":    "PyDriller unavailable for '{repo}'. Using GitHub API data only. Churn/hunk metrics will be absent.",
    },
    5: {
        "name":        "insufficient_commits",
        "trigger":     "Repo has < 10 commits in analysis window",
        "action":      "warn_continue",
        "transition":  RepoStatus.FETCHED,   # continues but flagged
        "continues":   True,
        "user_msg":    "'{repo}' has fewer than 10 commits in the window. Predictions are unreliable — results flagged as low-confidence.",
    },

    # ── MINE step failures ───────────────────

    6: {
        "name":        "no_python_files",
        "trigger":     "Radon finds 0 .py files (Go/JS/etc repo)",
        "action":      "skip_radon_keep_git",
        "transition":  RepoStatus.ANALYZED,  # continues with git data only, CC/MI = None
        "continues":   True,
        "user_msg":    "'{repo}' contains no Python files. Radon CC/MI skipped. Risk classification will use git-history signals only.",
    },
    7: {
        "name":        "radon_timeout",
        "trigger":     "radon subprocess does not return within 5 minutes",
        "action":      "skip_radon_keep_git",
        "transition":  RepoStatus.ANALYZED,
        "continues":   True,
        "user_msg":    "Radon timed out on '{repo}'. Complexity data unavailable — proceeding with git signals.",
    },
    8: {
        "name":        "clone_failed",
        "trigger":     "git clone exit code != 0",
        "action":      "skip_mine_use_git_only",
        "transition":  RepoStatus.FETCHED,   # stuck at FETCHED — no complexity
        "continues":   True,
        "user_msg":    "Could not clone '{repo}' locally. Radon analysis skipped. Risk will be assessed from git history alone.",
    },

    # ── ANALYZE / SCORE step failures ────────

    9: {
        "name":        "risk_agent_error",
        "trigger":     "Unhandled exception in RiskAgent or HealthScoreAgent",
        "action":      "emit_partial_result",
        "transition":  RepoStatus.FAILED,
        "continues":   True,
        "user_msg":    "Risk classification failed for '{repo}'. This repo will be excluded from the CEO report. All other repos continue.",
    },

    # ── REPORT step failures ─────────────────

    10: {
        "name":        "report_generation_failed",
        "trigger":     "CEOReportAgent raises an exception",
        "action":      "emit_raw_json_fallback",
        "transition":  RepoStatus.SCORED,    # report failed but score exists
        "continues":   True,
        "user_msg":    "CEO report generation encountered an error. Raw JSON output is available at peip_pipeline_output.json.",
    },

    # ── TOTAL WIPEOUT — the one stop condition ─

    11: {
        "name":        "zero_repos_have_data",
        "trigger":     "After FETCH step, every repo is SKIPPED or FAILED",
        "action":      "halt_pipeline",
        "transition":  None,
        "continues":   False,
        "user_msg":    (
            "Pipeline stopped: no usable data was returned for any repo.\n"
            "This means either (1) the GitHub username is wrong, (2) all repos are "
            "private and no token was provided, or (3) the analysis window returned "
            "0 commits for every repo.\n"
            "Action: verify your GitHub username and token, then retry."
        ),
    },
}


# ─────────────────────────────────────────────
# Handler functions — called by orchestrator
# ─────────────────────────────────────────────

def handle(scenario_id: int, ps: PipelineState,
           repo: str, exc: Exception | None = None) -> bool:
    """
    Apply a failure scenario to the pipeline state.
    Returns True if pipeline should continue, False if it should halt.
    Caller is responsible for calling halt logic if False is returned.
    """
    s = SCENARIOS[scenario_id]
    msg = s["user_msg"].format(repo=repo)

    if exc:
        detail = f"{type(exc).__name__}: {exc}"
    else:
        detail = None

    # Write to pipeline log
    level = "ERROR" if not s["continues"] else "WARN"
    ps.write_log(
        level  = level,
        step   = ps.current_step.name,
        repo   = repo,
        message = f"[Scenario {scenario_id}: {s['name']}] {msg}",
        payload = {"exception": detail} if detail else None
    )

    # Update repo status
    if repo in ps.repo_states and s["transition"] is not None:
        ps.repo_states[repo].status = s["transition"]
        ps.repo_states[repo].add_warning(msg)

    # Print user-facing message
    prefix = "  ! " if s["continues"] else "  ✗ "
    print(f"{prefix}{msg}")

    return s["continues"]


def check_total_wipeout(ps: PipelineState) -> bool:
    """
    Returns True if the pipeline should halt (scenario 11).
    Call after FETCH step completes.
    """
    if not ps.any_data_at_all:
        handle(11, ps, repo="[ALL REPOS]", exc=None)
        return True
    return False


def should_skip_repo(ps: PipelineState, repo: str) -> bool:
    """True if this repo should be skipped at any step."""
    rs = ps.repo_states.get(repo)
    return rs is not None and rs.status in (RepoStatus.SKIPPED, RepoStatus.FAILED)
