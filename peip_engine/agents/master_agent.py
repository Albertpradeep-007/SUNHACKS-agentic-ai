"""
MasterAgent — PEIP Intelligence Layer Orchestrator

Receives session config from InputAgent.
Calls GitHistoryAgent -> ComplexityAgent -> RiskAgent -> CEOReportAgent in
strict sequence, passing each output forward.

Responsibilities:
  - Does NOT analyze code itself
  - Handles per-repo failures gracefully (skip and log, never stop pipeline)
  - Collects all outputs into a unified final_output dict
  - Passes final_output to DashboardAgent (User Layer)
"""

import uuid
import traceback
from datetime import datetime


def run_pipeline(session_config: dict) -> dict:
    """
    Orchestrate the full 4-agent Intelligence Layer pipeline.
    Returns the final_output dict for DashboardAgent.
    """
    from git_history_agent  import git_history_agent_pydriller
    from complexity_agent  import complexity_agent
    from risk_agent         import risk_agent
    from ceo_report_agent  import ceo_report_agent

    session_id       = str(uuid.uuid4())[:8]
    repos            = session_config.get("repos", [])
    github_username  = session_config.get("github_username", "")
    token            = session_config.get("token")
    window_days      = session_config.get("analysis_window_days", 90)

    repos_analyzed: list[str] = []
    repos_skipped:  list[str] = []
    pipeline_warnings: list[str] = list(session_config.get("warnings", []))

    git_history_all:  dict = {}
    complexity_all:   dict = {}
    risk_all:         dict = {}

    print(f"\n[MasterAgent] Session {session_id} — {len(repos)} repo(s) queued")
    print(f"[MasterAgent] Analysis window: {window_days} days\n")

    # ─────────────────────────────────────────────
    # STEP 1 — GitHistoryAgent (per repo)
    # ─────────────────────────────────────────────
    print("[MasterAgent] Step 1 → GitHistoryAgent")
    for repo in repos:
        try:
            repo_url = f"https://github.com/{github_username}/{repo}.git"
            result = git_history_agent_pydriller(
                repo_name=repo,
                repo_path=repo_url,
                window_days=window_days,
                token=token
            )
            git_history_all[repo] = result
            repos_analyzed.append(repo)
            print(f"  [OK] {repo}")
        except Exception as e:
            repos_skipped.append(repo)
            pipeline_warnings.append(
                f"GitHistoryAgent failed on '{repo}': {type(e).__name__}: {e}"
            )
            print(f"  [SKIP] {repo} — {type(e).__name__}: {e}")

    if not repos_analyzed:
        pipeline_warnings.append("GitHistoryAgent returned no data. Pipeline cannot continue.")
        return _build_empty_output(session_id, repos_skipped, pipeline_warnings)

    # ─────────────────────────────────────────────
    # STEP 2 — ComplexityAgent (per repo)
    # ─────────────────────────────────────────────
    print("\n[MasterAgent] Step 2 → ComplexityAgent")
    for repo in repos_analyzed[:]:  # iterate copy so removals don't break loop
        git_out = git_history_all.get(repo, {})
        try:
            result = complexity_agent(
                repo_name=repo,
                github_username=github_username,
                token=token,
                git_history=git_out
            )
            if result is None:
                complexity_all[repo] = None
                pipeline_warnings.append(
                    f"ComplexityAgent: no Python files found in '{repo}' — CC/MI skipped."
                )
                print(f"  [WARN] {repo} — no Python files")
            else:
                complexity_all[repo] = result
                print(f"  [OK] {repo}")
        except Exception as e:
            complexity_all[repo] = None
            pipeline_warnings.append(
                f"ComplexityAgent failed on '{repo}': {type(e).__name__}: {e}"
            )
            print(f"  [WARN] {repo} — {type(e).__name__}: {e}")

    # ─────────────────────────────────────────────
    # STEP 3 — RiskAgent (per repo, uses both outputs)
    # ─────────────────────────────────────────────
    print("\n[MasterAgent] Step 3 → RiskAgent")
    for repo in repos_analyzed:
        try:
            result = risk_agent(
                repo_name=repo,
                git_history=git_history_all.get(repo, {}),
                complexity=complexity_all.get(repo)
            )
            risk_all[repo] = result
            print(f"  [OK] {repo} → {result.get('repo_classification','?')}")
        except Exception as e:
            pipeline_warnings.append(
                f"RiskAgent failed on '{repo}': {type(e).__name__}: {e}"
            )
            # Provide a minimal fallback so CEOReportAgent doesn't break
            risk_all[repo] = {
                "repo": repo,
                "components": [],
                "repo_classification": "UNKNOWN",
                "primary_signal": f"Risk analysis failed: {e}"
            }
            print(f"  [WARN] {repo} — {type(e).__name__}: {e}")

    # ─────────────────────────────────────────────
    # STEP 4 — CEOReportAgent (cross-repo synthesis)
    # ─────────────────────────────────────────────
    print("\n[MasterAgent] Step 4 → CEOReportAgent")
    try:
        ceo_report = ceo_report_agent(
            risk_output=risk_all,
            complexity_output=complexity_all,
            git_history_output=git_history_all
        )
        print("  [OK] CEO report generated")
    except Exception as e:
        ceo_report = f"CEO report generation failed: {e}\n{traceback.format_exc()}"
        pipeline_warnings.append(f"CEOReportAgent failed: {e}")
        print(f"  [WARN] CEO report failed — {e}")

    # ─────────────────────────────────────────────
    # STEP 5 — Assemble final output for DashboardAgent
    # ─────────────────────────────────────────────
    final_output = {
        "session_id":        session_id,
        "generated_at":      datetime.now().isoformat(),
        "repos_analyzed":    repos_analyzed,
        "repos_skipped":     repos_skipped,
        "git_history":       git_history_all,
        "complexity":        complexity_all,
        "risk_flags":        risk_all,
        "ceo_report":        ceo_report,
        "pipeline_warnings": pipeline_warnings
    }

    print(f"\n[MasterAgent] Pipeline complete — {len(repos_analyzed)} analyzed, "
          f"{len(repos_skipped)} skipped, {len(pipeline_warnings)} warnings.")

    return final_output


def _build_empty_output(session_id, repos_skipped, warnings):
    return {
        "session_id":        session_id,
        "generated_at":      datetime.now().isoformat(),
        "repos_analyzed":    [],
        "repos_skipped":     repos_skipped,
        "git_history":       {},
        "complexity":        {},
        "risk_flags":        {},
        "ceo_report":        "Pipeline produced no data.",
        "pipeline_warnings": warnings
    }


if __name__ == "__main__":
    # Quick smoke-test using demo session config
    demo_config = {
        "github_username": "chaitu-png",
        "repos": ["fintech-core-v2", "socialhive-api", "THIRD-PROJECT"],
        "token": None,
        "analysis_window_days": 90,
        "scope": "all_repos",
        "warnings": []
    }
    import json
    out = run_pipeline(demo_config)
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("git_history", "complexity", "risk_flags")}, indent=2))
