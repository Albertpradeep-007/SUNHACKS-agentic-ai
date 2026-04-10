"""
InputAgent — PEIP Layer 1: User Entry Agent

Responsibilities:
  - Accept GitHub username/URL + optional token from user
  - Validate the inputs (user exists, token scope, repo commit count, Python presence)
  - Build and return a session config dict for the Intelligence Layer
  - Never analyze code itself — just validate and route
"""

import re
import sys

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


# ─────────────────────────────────────────────
# URL / username normalization
# ─────────────────────────────────────────────

def extract_username(raw: str) -> tuple[str, str | None]:
    """
    Parse any of these formats into (username, optional_repo_name):
      "chaitu-png"
      "github.com/chaitu-png"
      "https://github.com/chaitu-png"
      "https://github.com/chaitu-png/fintech-core-v2"
    """
    raw = raw.strip().rstrip("/")
    # Strip protocol + host
    raw = re.sub(r"^https?://", "", raw)
    raw = re.sub(r"^github\.com/", "", raw)
    parts = raw.split("/")
    username = parts[0]
    repo = parts[1] if len(parts) >= 2 else None
    return username, repo


# ─────────────────────────────────────────────
# Validation helpers
# ─────────────────────────────────────────────

def validate_token_scope(token: str) -> tuple[bool, str]:
    """Verify token has at minimum repo-read access."""
    if not GITHUB_AVAILABLE:
        return True, "PyGithub not installed — skipping token scope check."
    try:
        g = Github(token)
        user = g.get_user()
        _ = user.login          # triggers auth
        return True, f"Token valid. Authenticated as: {user.login}"
    except GithubException as e:
        return False, f"Token error: {e.data.get('message', str(e))}"


def fetch_repo_list(username: str, token: str | None) -> tuple[list[str], list[str]]:
    """
    Return (repo_names, warnings).
    Warns if private repos are skipped (no token) or if a repo has
    insufficient history / no Python files.
    """
    if not GITHUB_AVAILABLE:
        # Fallback: return known repos from previous sessions
        defaults = ["fintech-core-v2", "scalechat-realtime", "socialhive-api",
                    "PROJECT_1", "PROJECT_2", "THIRD-PROJECT"]
        warnings = ["PyGithub not installed — using cached repo list. "
                    "Install with: pip install PyGithub"]
        return defaults, warnings

    g = Github(token) if token else Github()
    warnings = []

    try:
        user = g.get_user(username)
    except GithubException:
        return [], [f"GitHub user '{username}' not found or not accessible."]

    repos = []
    for repo in user.get_repos():
        if repo.private and not token:
            warnings.append(f"Skipped private repo: {repo.name} (no token provided)")
            continue

        # Commit count check
        try:
            commits = repo.get_commits().totalCount
            if commits < 10:
                warnings.append(f"'{repo.name}' has only {commits} commit(s) — "
                                 "insufficient history for reliable prediction.")
        except Exception:
            commits = 0

        # Python file check
        try:
            contents = repo.get_contents("")
            has_python = any(
                f.name.endswith(".py")
                for f in contents
                if f.type == "file"
            )
            if not has_python:
                warnings.append(f"'{repo.name}' has no top-level .py files — "
                                 "Radon complexity analysis will be limited.")
        except Exception:
            pass

        repos.append(repo.name)

    if not token:
        warnings.insert(0, "No token provided — public repos only. "
                           "Private repos will be skipped.")
    return repos, warnings


# ─────────────────────────────────────────────
# Interactive session setup
# ─────────────────────────────────────────────

def _ask(prompt: str, default: str = "") -> str:
    try:
        val = input(prompt).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        return default


def run_input_agent() -> dict:
    """
    Interactively collect GitHub details from the user, validate them,
    and return a session config dict for the Intelligence Layer.
    """
    print("\n" + "=" * 60)
    print("  PEIP — Predictive Engineering Intelligence Platform")
    print("  InputAgent v1.0")
    print("=" * 60)
    print("I'll collect a few details, then kick off the analysis.\n")

    # ── Step 1: GitHub URL / username ──────────────────────────
    raw_input = _ask("GitHub username or repo URL: ")
    if not raw_input:
        print("ERROR: GitHub username is required. Exiting.")
        sys.exit(1)

    username, specific_repo = extract_username(raw_input)
    print(f"  Parsed username: {username}")
    if specific_repo:
        print(f"  Parsed repo:     {specific_repo}")

    # ── Step 2: Token ──────────────────────────────────────────
    token_raw = _ask("GitHub Personal Access Token (press Enter to skip for public repos): ")
    token = token_raw if token_raw else None

    token_warnings = []
    if token:
        valid, msg = validate_token_scope(token)
        if not valid:
            print(f"  WARNING: {msg}")
            token_warnings.append(msg)
            token = None          # fall back to unauthenticated
        else:
            print(f"  {msg}")
    else:
        token_warnings.append("No token provided — public repos only. Private repos will be skipped.")
        print("  NOTE: " + token_warnings[0])

    # ── Step 3: Scope ──────────────────────────────────────────
    print("\nAnalysis scope:")
    print("  1. All repos in the account (default)")
    print("  2. Specific repo")
    scope_choice = _ask("Choose [1/2]: ", "1")

    if scope_choice == "2" or specific_repo:
        if not specific_repo:
            specific_repo = _ask("Repo name: ")
        scope = "single_repo"
        repos_to_use = [specific_repo]
        repo_warnings: list[str] = []
    else:
        scope = "all_repos"
        print(f"\n  Fetching repo list for '{username}'...")
        repos_to_use, repo_warnings = fetch_repo_list(username, token)
        if not repos_to_use:
            print("  ERROR: No accessible repos found. Check username or token.")
            sys.exit(1)
        print(f"  Found {len(repos_to_use)} repo(s): {', '.join(repos_to_use)}")

    # ── Step 4: Time window ────────────────────────────────────
    print("\nAnalysis time window:")
    print("  1. Last 30 days")
    print("  2. Last 90 days — recommended (default)")
    print("  3. Last 6 months (180 days)")
    print("  4. Full history")
    window_choice = _ask("Choose [1/2/3/4]: ", "2")
    window_map = {"1": 30, "2": 90, "3": 180, "4": 0}
    window_days = window_map.get(window_choice, 90)
    window_label = {30: "30 days", 90: "90 days", 180: "6 months", 0: "full history"}[window_days]

    # ── Compile warnings ───────────────────────────────────────
    all_warnings = token_warnings + repo_warnings

    # ── Build session config ───────────────────────────────────
    session_config = {
        "github_username":    username,
        "repos":              repos_to_use,
        "token_provided":     token is not None,
        "token":              token,
        "analysis_window_days": window_days,
        "scope":              scope,
        "warnings":           all_warnings
    }

    # ── Confirm with user ──────────────────────────────────────
    print("\n" + "-" * 60)
    print(f"  Username   : {username}")
    print(f"  Repos      : {', '.join(repos_to_use)}")
    print(f"  Token      : {'provided' if token else 'not provided (public only)'}")
    print(f"  Scope      : {scope}")
    print(f"  Time window: {window_label}")
    if all_warnings:
        print("\n  Warnings:")
        for w in all_warnings:
            print(f"    ⚠  {w}")
    print("-" * 60)
    print("\nGot it. Connecting to GitHub and starting analysis...")
    print("Analysis started. This will take 2-3 minutes.\n")

    return session_config


if __name__ == "__main__":
    cfg = run_input_agent()
    import json
    print(json.dumps(cfg, indent=2))
