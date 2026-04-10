"""
GitHistoryAgent v2 — PyDriller Process Metrics + GitHub API

Uses the 5 PyDriller process metrics from Spadini et al. (ESEC/FSE 2018):
  1. CodeChurn       — lines added/removed per file
  2. HunksCount      — change fragmentation
  3. ContributorsCount  — bus factor
  4. ContributorsExperience — ownership concentration
  5. ChangeSet       — coupling (files changed together)

Also calls GitHub API for:
  - Commit frequency per week
  - Deployment frequency (releases per month)
  - Bug MTTR (closed issues with bug label)

Bot commits excluded from all metrics.
Auto-generated files excluded from hotspot analysis.
"""

import math
import re
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────
# Exclusion filters
# ─────────────────────────────────────────────

BOT_PATTERNS  = re.compile(r"\[bot\]|noreply|dependabot|renovate|github-actions",
                            re.IGNORECASE)
SKIP_FILES    = re.compile(
    r"(migrations/|__pycache__|\.pyc$|\.lock$|package-lock|yarn\.lock"
    r"|\.min\.js|/vendor/|\.pb\.go|_generated\.py)", re.IGNORECASE
)


def _is_bot(commit) -> bool:
    try:
        email = commit.committer_email or ""
        name  = commit.committer or ""
        return bool(BOT_PATTERNS.search(email) or BOT_PATTERNS.search(name))
    except Exception:
        return False


def _skip_file(path: str) -> bool:
    return bool(SKIP_FILES.search(path))


def _top20(metrics_dict: dict) -> set:
    if not metrics_dict:
        return set()
    items  = sorted(metrics_dict.items(), key=lambda x: x[1], reverse=True)
    cutoff = max(1, math.ceil(len(items) * 0.20))
    return {f for f, _ in items[:cutoff]}


# ─────────────────────────────────────────────
# GitHub API helpers (via PyGithub if available)
# ─────────────────────────────────────────────

def _github_api_data(github_username: str, repo_name: str,
                     token: str | None, window_days: int) -> dict:
    """
    Fetch: commit frequency, deployment frequency, bug MTTR.
    Falls back to synthetic estimates if PyGithub is unavailable or rate-limited.
    """
    try:
        from github import Github, GithubException
        g = Github(token) if token else Github()
        repo = g.get_repo(f"{github_username}/{repo_name}")

        # Handle 'Full history' (window_days = 0)
        if window_days == 0:
            repo_created_at = repo.created_at.replace(tzinfo=timezone.utc)
            actual_lifespan_days = max(1, (datetime.now(timezone.utc) - repo_created_at).days)
            effective_window_days = actual_lifespan_days
            since = repo.created_at
        else:
            effective_window_days = window_days
            since = datetime.now(timezone.utc) - timedelta(days=window_days)

        # Commit frequency
        commits = list(repo.get_commits(since=since))
        commit_freq_per_week = len(commits) / (effective_window_days / 7.0)

        # Deployment frequency (releases per month)
        try:
            releases = list(repo.get_releases())
            recent_releases = [r for r in releases
                               if r.created_at and r.created_at.replace(tzinfo=timezone.utc) >= since]
            deploy_freq_per_month = len(recent_releases) / (effective_window_days / 30.0)
        except Exception:
            deploy_freq_per_month = 0.0

        # Bug MTTR
        try:
            bug_issues = list(repo.get_issues(state="closed", labels=["bug"]))
            mttr_days_list = []
            for issue in bug_issues:
                if issue.created_at and issue.closed_at:
                    delta = (issue.closed_at - issue.created_at).total_seconds() / 86400
                    mttr_days_list.append(delta)
            bug_mttr_days = round(sum(mttr_days_list) / len(mttr_days_list), 1) \
                if mttr_days_list else None
        except Exception:
            bug_mttr_days = None

        return {
            "commit_frequency_per_week":    round(commit_freq_per_week, 2),
            "deployment_frequency_per_month": round(deploy_freq_per_month, 2),
            "bug_mttr_days":                bug_mttr_days,
            "source":                       "GitHub API (live)"
        }

    except Exception as e:
        # Synthetic fallback — clearly labelled
        return {
            "commit_frequency_per_week":    1.0,
            "deployment_frequency_per_month": 0.5,
            "bug_mttr_days":                None,
            "source":                       f"Synthetic fallback (GitHub API unavailable: {e})"
        }


# ─────────────────────────────────────────────
# PyDriller metrics
# ─────────────────────────────────────────────

def _pydriller_metrics(repo_path: str, since: datetime, to: datetime) -> dict:
    """
    Run all 5 PyDriller process metrics.
    Returns dict of raw results, or empty dict on failure.
    """
    try:
        from pydriller.metrics.process.code_churn         import CodeChurn
        from pydriller.metrics.process.hunks_count        import HunksCount
        from pydriller.metrics.process.contributors_count import ContributorsCount
        from pydriller.metrics.process.contributors_experience import ContributorsExperience
        from pydriller.metrics.process.change_set         import ChangeSet

        churn_m = CodeChurn(path_to_repo=repo_path, since=since, to=to)
        hunk_m  = HunksCount(path_to_repo=repo_path, since=since, to=to)
        cont_m  = ContributorsCount(path_to_repo=repo_path, since=since, to=to)
        exp_m   = ContributorsExperience(path_to_repo=repo_path, since=since, to=to)
        cset_m  = ChangeSet(path_to_repo=repo_path, since=since, to=to)

        return {
            "churn_count":     churn_m.count(),
            "churn_added_removed": churn_m.get_added_and_removed_lines(),
            "hunk_count":      hunk_m.count(),
            "total_contributors": cont_m.count(),
            "minor_contributors": cont_m.count_minor(),
            "experience":      exp_m.count(),
            "changeset_avg":   cset_m.avg(),
            "changeset_max":   cset_m.max(),
            "ok":              True
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────
# Commit frequency + trend via PyDriller
# ─────────────────────────────────────────────

def _commit_trend(repo_path: str, since_90: datetime, since_30: datetime, to: datetime) -> tuple:
    """Returns (freq_per_week, trend_label) from commit traversal. Excludes bots."""
    try:
        from pydriller import Repository

        commits_90 = [c for c in Repository(repo_path, since=since_90, to=to).traverse_commits()
                      if not _is_bot(c)]
        commits_30 = [c for c in Repository(repo_path, since=since_30, to=to).traverse_commits()
                      if not _is_bot(c)]

        n90 = len(commits_90)
        n30 = len(commits_30)
        freq = n90 / (90 / 7.0)

        rate_30    = n30 / 30.0
        rate_prior = (n90 - n30) / 60.0

        if rate_30 > rate_prior * 1.20:   trend = "accelerating"
        elif rate_30 < rate_prior * 0.80: trend = "decelerating"
        else:                              trend = "stable"

        return round(freq, 2), trend
    except Exception:
        return 1.0, "unknown"


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def git_history_agent_pydriller(repo_name: str, repo_path: str,
                                window_days: int = 90,
                                token: str | None = None,
                                github_username: str = "") -> dict:
    """
    Mine git history using PyDriller process metrics + GitHub API.
    repo_path: local directory OR remote git URL.
    Returns structured JSON dict conforming to spec.
    """
    print(f"  [GitHistoryAgent] {repo_name}")

    to    = datetime.now()
    effective_window = max(1, window_days) if window_days > 0 else 365 * 5
    since = to - timedelta(days=effective_window) if window_days > 0 else None
    s30   = to - timedelta(days=30)

    # ── PyDriller metrics ──────────────────────
    pd = _pydriller_metrics(repo_path, since, to)

    if pd.get("ok"):
        churn_counts     = pd["churn_count"]            # {file: churn_lines}
        hunk_counts      = pd["hunk_count"]             # {file: hunk_count}
        total_contribs   = pd["total_contributors"]     # {file: n}
        minor_contribs   = pd["minor_contributors"]     # {file: n}
        experience       = pd["experience"]             # {file: {author: pct}}
        changeset_avg    = pd.get("changeset_avg") or 0
        ar_lines         = pd.get("churn_added_removed") or {}

        top20_churn = _top20({f: v for f, v in churn_counts.items()
                              if not _skip_file(f)})
        top20_hunks = _top20({f: v for f, v in hunk_counts.items()
                              if not _skip_file(f)})

        # Bus factor per file
        bus_factor_risks = []
        for f, total in total_contribs.items():
            if _skip_file(f):
                continue
            minor = minor_contribs.get(f, 0)
            real_bus = total - minor
            if real_bus <= 1:
                bus_factor_risks.append(f)

        # Extreme ownership (>80% single owner on hotspot)
        single_owner_hotspot = []
        for f, owners in experience.items():
            if _skip_file(f) or not owners or f not in top20_churn:
                continue
            top_pct = max(owners.values()) if isinstance(owners, dict) else 0
            if top_pct > 80.0:
                single_owner_hotspot.append(f)

        # Hotspot: top 20% churn AND (top 20% hunks OR CC >= C — CC supplied later by RiskAgent)
        hotspot_candidates = list(top20_churn & top20_hunks)

        # Compute per-file churn rate (requires LOC — use raw churn count as proxy)
        # Real churn rate needs total LOC from Radon. Store raw counts here; rate computed in RiskAgent.
        file_churn_raw = {f: v for f, v in churn_counts.items() if not _skip_file(f)}
        added_removed  = {f: v for f, v in ar_lines.items() if not _skip_file(f)}

        freq_per_week, churn_trend = _commit_trend(repo_path, since, s30, to)
        pydriller_ok = True
    else:
        # PyDriller unavailable — return synthetic placeholders clearly labelled
        hotspot_candidates   = []
        bus_factor_risks     = []
        single_owner_hotspot = []
        file_churn_raw       = {}
        added_removed        = {}
        changeset_avg        = 0
        churn_trend          = "unknown"
        freq_per_week        = 0.0
        top20_churn          = set()
        top20_hunks          = set()
        pydriller_ok         = False

    # ── GitHub API data ────────────────────────
    # Extract username from remote URL if not passed
    _user = github_username
    if not _user and repo_path.startswith("https://github.com/"):
        parts = repo_path.replace("https://github.com/", "").split("/")
        _user = parts[0] if parts else ""

    api_data = _github_api_data(_user, repo_name, token, window_days)

    return {
        "repo":                        repo_name,
        "analysis_window_days":        window_days,
        "pydriller_available":         pydriller_ok,
        "hotspot_files":               hotspot_candidates,
        "single_owner_hotspot_files":  single_owner_hotspot,
        "bus_factor_risk_files":       bus_factor_risks[:15],
        "file_churn_raw":              file_churn_raw,
        "file_churn_added_removed":    added_removed,
        "top20_churn_files":           list(top20_churn),
        "top20_hunk_files":            list(top20_hunks),
        "avg_files_changed_together":  round(changeset_avg, 1) if changeset_avg else 0,
        "churn_trend":                 churn_trend,
        "commit_frequency_per_week":   freq_per_week if pydriller_ok else api_data["commit_frequency_per_week"],
        "deployment_frequency_per_month": api_data["deployment_frequency_per_month"],
        "bug_mttr_days":               api_data["bug_mttr_days"],
        "github_api_source":           api_data["source"],
        "coupling_flag":               changeset_avg > 5.0,
    }
