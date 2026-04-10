"""
PEIP Orchestrator — Real State Machine

Replaces the descriptive MasterAgent with an actual loop that:

  Per repo, per step:
    1. Checks pre-conditions before calling the agent
    2. Makes the call/skip decision
    3. Validates agent output against the handoff contract
    4. Transitions state correctly on success or failure
    5. Writes to the pipeline log at every step
    6. Gates on the one stop-condition: zero repos have any data

Pipeline steps per repo:
  FETCH    → GitHistoryAgent    (PyDriller + GitHub API)
  MINE     → ComplexityAgent    (Radon CC/MI/RAW + TDI)
  ANALYZE  → RiskAgent          (signal-level classification)
  SCORE    → HealthScoreAgent   (signal summary)
  REPORT   → CEOReportAgent     (cross-repo — runs once per pipeline)
  DELIVER  → DashboardAgent     (render to user)

Every failure scenario is handled explicitly by failure_handler.py.
The only stop condition is Scenario 11: zero repos have any data at all.
"""

import json
import traceback
from datetime import datetime

from pipeline_state  import PipelineState, RepoState, RepoStatus, Step, new_pipeline_state
from failure_handler import handle, check_total_wipeout, should_skip_repo, SCENARIOS
from agent_handoffs  import (
    build_fetch_payload, build_fetch_repo_args,
    build_mine_payload, build_analyze_payload,
    build_report_payload, build_deliver_payload,
    validate_agent_output,
    EXPECTED_GIT_HISTORY_KEYS, EXPECTED_COMPLEXITY_KEYS, EXPECTED_RISK_KEYS,
)
from workspace_manager import WorkspaceManager


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _banner(step: str, detail: str = "") -> None:
    pad = 56 - len(step) - len(detail)
    print(f"\n{'-'*56}")
    print(f"  STEP: {step}{'  ' + detail if detail else ''}")
    print(f"{'-'*56}")


def _ok(repo: str, note: str = "") -> None:
    suffix = f"  ({note})" if note else ""
    print(f"  [OK ]  {repo}{suffix}")


def _skip(repo: str, reason: str) -> None:
    print(f"  [SKIP] {repo} — {reason}")


# ─────────────────────────────────────────────
# STEP 1 — FETCH
# ─────────────────────────────────────────────

def _step_fetch(ps: PipelineState, wm: WorkspaceManager) -> None:
    from git_history_agent import git_history_agent_pydriller

    _banner("FETCH", "GitHistoryAgent — PyDriller + GitHub API")
    ps.transition("IDLE", "FETCH")
    ps.current_step = Step.FETCH

    fetch_payload = build_fetch_payload(ps)

    for repo in ps.repos:
        rs = ps.repo_states[repo]
        rs.started_at = datetime.now().isoformat()
        ps.current_repo = repo
        ps.info("FETCH", repo, f"Starting fetch for {repo}")

        args = build_fetch_repo_args(repo, fetch_payload)
        
        # Power Layer: Local Workspace Deep Clone
        with wm.clone_repo(f"https://github.com/{ps.github_username}/{repo}", repo, ps.token) as local_path:
            rs.local_path = local_path
            
        if rs.local_path:
            args["repo_path"] = rs.local_path

        try:
            result = git_history_agent_pydriller(**args)

            # Validate output contract
            warnings = validate_agent_output(result, EXPECTED_GIT_HISTORY_KEYS,
                                             "GitHistoryAgent", repo)
            for w in warnings:
                ps.warn("FETCH", repo, w)

            # Check insufficient commits
            commit_freq = result.get("commit_frequency_per_week", 0)
            eff_window = max(1, ps.analysis_window_days)
            if ps.analysis_window_days > 0 and commit_freq < (10 / (eff_window / 7.0)):
                handle(5, ps, repo)   # Scenario 5: insufficient commits (warn, continue)
                rs.add_warning(f"Commit frequency {commit_freq:.2f}/week — low confidence.")
            elif ps.analysis_window_days == 0 and commit_freq < 0.5:
                handle(5, ps, repo)
                rs.add_warning(f"Commit frequency {commit_freq:.2f}/week — low confidence.")

            rs.git_history = result
            rs.pydriller_failed  = not result.get("pydriller_available", True)
            rs.github_api_failed = "Synthetic fallback" in result.get("github_api_source", "")

            if rs.pydriller_failed:
                handle(4, ps, repo)   # Scenario 4: PyDriller unavailable

            rs.status = RepoStatus.FETCHED
            ps.info("FETCH", repo, f"Fetched OK. pydriller={result.get('pydriller_available')}")
            _ok(repo, f"churn_trend={result.get('churn_trend','?')}, "
                      f"hotspots={len(result.get('hotspot_files',[]))}")

        except Exception as exc:
            err_str = str(exc).lower()
            if "404" in err_str or "not found" in err_str:
                handle(1, ps, repo, exc)    # Scenario 1: repo not found
            elif "401" in err_str or "403" in err_str or "auth" in err_str:
                handle(2, ps, repo, exc)    # Scenario 2: auth failure
            elif "rate" in err_str:
                handle(3, ps, repo, exc)    # Scenario 3: rate limited
            else:
                ps.error("FETCH", repo, f"Unexpected error: {exc}")
                rs.status = RepoStatus.FAILED
                rs.add_warning(f"GitHistoryAgent failed: {type(exc).__name__}: {exc}")
                _skip(repo, f"{type(exc).__name__}: {exc}")

    ps.transition("FETCH", "MINE")


# ─────────────────────────────────────────────
# STEP 2 — MINE
# ─────────────────────────────────────────────

def _step_mine(ps: PipelineState) -> None:
    from complexity_agent import complexity_agent

    _banner("MINE", "ComplexityAgent — Radon CC/MI/RAW + TDI")
    ps.current_step = Step.MINE

    for repo in ps.repos:
        rs = ps.repo_states[repo]

        if should_skip_repo(ps, repo):
            _skip(repo, f"status={rs.status.value}")
            continue

        if rs.git_history is None:
            ps.warn("MINE", repo, "No git_history — skipping Radon")
            handle(8, ps, repo)     # Scenario 8: clone failed / no git data
            continue

        ps.info("MINE", repo, "Building complexity payload")
        mine_payload = build_mine_payload(repo, ps, rs.git_history)

        try:
            # Power Layer: Use local workspace path for Radon analysis!
            path_to_analyze = rs.local_path if rs.local_path else mine_payload["repo_name"]
            
            result = complexity_agent(
                repo_name       = mine_payload["repo_name"],
                github_username = mine_payload["github_username"],
                token           = mine_payload["token"],
                git_history     = mine_payload["git_history"],
                local_repo_path = rs.local_path
            )

            if result is None:
                handle(6, ps, repo)  # Scenario 6: no Python files
                rs.no_python_files = True
                rs.complexity = None
                # Keep status as FETCHED — ANALYZE can still run on git signals
            else:
                warnings = validate_agent_output(result, EXPECTED_COMPLEXITY_KEYS,
                                                 "ComplexityAgent", repo)
                for w in warnings:
                    ps.warn("MINE", repo, w)
                rs.complexity = result
                rs.status = RepoStatus.ANALYZED
                n_files = result.get("repo_summary", {}).get("total_python_files", 0)
                pct_c   = result.get("repo_summary", {}).get("pct_grade_C_or_worse", 0)
                _ok(repo, f"{n_files} py files, {pct_c:.0%} grade C+")
                ps.info("MINE", repo, f"Complexity OK — {n_files} files, {pct_c:.0%} grade C+")

        except Exception as exc:
            ps.error("MINE", repo, traceback.format_exc())
            if "timeout" in str(exc).lower() or "TimeoutExpired" in type(exc).__name__:
                handle(7, ps, repo, exc)    # Scenario 7: Radon timeout
            else:
                ps.error("MINE", repo, f"ComplexityAgent error: {exc}")
                rs.add_warning(f"ComplexityAgent failed: {type(exc).__name__}: {exc}")
                _skip(repo, f"{type(exc).__name__}: {exc}")

    ps.transition("MINE", "ANALYZE")


# ─────────────────────────────────────────────
# STEP 3 — ANALYZE
# ─────────────────────────────────────────────

def _step_analyze(ps: PipelineState) -> None:
    from risk_agent import risk_agent

    _banner("ANALYZE", "RiskAgent — signal-level classification")
    ps.current_step = Step.ANALYZE

    for repo in ps.repos:
        rs = ps.repo_states[repo]

        if should_skip_repo(ps, repo):
            _skip(repo, f"status={rs.status.value}")
            continue

        ps.info("ANALYZE", repo, "Building risk analysis payload")
        payload = build_analyze_payload(
            repo       = repo,
            git_history_out = rs.git_history or {},
            complexity_out  = rs.complexity,
        )

        try:
            result = risk_agent(
                repo_name  = payload["repo_name"],
                git_history = payload["git_history"],
                complexity  = payload["complexity"],
            )
            warnings = validate_agent_output(result, EXPECTED_RISK_KEYS,
                                             "RiskAgent", repo)
            for w in warnings:
                ps.warn("ANALYZE", repo, w)

            rs.risk   = result
            rs.status = RepoStatus.SCORED
            cls       = result.get("repo_classification", "?")
            n_crit    = result.get("critical_count", 0)
            _ok(repo, f"{cls}, {n_crit} critical components")
            ps.info("ANALYZE", repo, f"Risk OK — classification={cls}")

        except Exception as exc:
            handle(9, ps, repo, exc)   # Scenario 9: risk agent error
            ps.error("ANALYZE", repo, traceback.format_exc())

    ps.transition("ANALYZE", "SCORE")


# ─────────────────────────────────────────────
# STEP 4 — SCORE (signal summary per repo)
# ─────────────────────────────────────────────

def _step_score(ps: PipelineState) -> None:
    from peip_analytics import health_score_agent as _hsa

    _banner("SCORE", "HealthScoreAgent — signal summary")
    ps.current_step = Step.SCORE

    for repo in ps.repos:
        rs = ps.repo_states[repo]

        if should_skip_repo(ps, repo) or rs.risk is None:
            _skip(repo, "no risk data")
            continue

        try:
            # HealthScoreAgent from peip_analytics uses repo name to look up
            # the built-in simulated profile. When running live, we build a
            # lightweight health dict directly from the risk output.
            if rs.risk.get("repo_classification") in ("CRITICAL", "AT RISK", "STABLE", "HEALTHY"):
                # Live mode: derive health dict from risk output
                risk    = rs.risk
                git     = rs.git_history or {}
                cmplx   = rs.complexity   or {}
                files   = cmplx.get("files", {})

                # Worst CC
                cc_grades = [f.get("cc_grade", "A") for f in files.values()]
                order     = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
                worst_g   = max(cc_grades, key=lambda g: order.get(g, 0)) if cc_grades else "A"
                worst_cc  = max((f.get("cc_max", 1) for f in files.values()), default=1)

                rs.health = {
                    "repository":           repo,
                    "classification":       risk.get("repo_classification", "UNKNOWN"),
                    "classification_reason": risk.get("primary_signal", ""),
                    "flags_triggered":      [
                        sig for comp in risk.get("components", [])
                        for sig in comp.get("signals_triggered", [])
                    ],
                    "signals": {
                        "cyclomatic_complexity": {
                            "value": worst_cc,
                            "grade": worst_g,
                            "source": "McCabe 1976, IEEE + Radon docs"
                        },
                        "code_churn": {
                            "rate": git.get("churn_trend", "unknown"),
                            "label": git.get("churn_trend", "unknown"),
                            "source": "Munson & Elbaum 1998"
                        },
                        "bus_factor": {
                            "value": len(git.get("bus_factor_risk_files", [])),
                            "source": "Spadini et al. 2018"
                        },
                        "hotspot": {
                            "triggered": bool(git.get("hotspot_files")),
                            "source": "arXiv 2026"
                        },
                        "dora": {
                            "archetype": "See risk_flags",
                            "source": "DORA 2024/2025"
                        }
                    }
                }
                rs.status = RepoStatus.REPORTED
                _ok(repo, risk.get("repo_classification", "?"))
            else:
                # Demo mode fallback — use built-in simulated profiles
                rs.health = _hsa(repo)
                rs.status = RepoStatus.REPORTED
                _ok(repo, rs.health.get("classification", "?"))

        except Exception as exc:
            handle(9, ps, repo, exc)   # reuse Scenario 9 for SCORE failures
            ps.error("SCORE", repo, traceback.format_exc())

    ps.transition("SCORE", "PATCH")


# ─────────────────────────────────────────────
# STEP 4.5 — PATCH (Ollama refactoring)
# ─────────────────────────────────────────────

def _step_patch(ps: PipelineState) -> None:
    from patch_agent import run_patch_agent

    _banner("PATCH", "PatchAgent — Ollama Code Refactoring & Syntax Checking")
    ps.current_step = Step.PATCH

    for repo in ps.repos:
        rs = ps.repo_states[repo]

        if should_skip_repo(ps, repo) or not rs.complexity or not rs.local_path:
            _skip(repo, "no complexity data or local workspace")
            continue

        try:
            ps.info("PATCH", repo, "Querying Ollama LLaMa3 for patches...")
            patch_res = run_patch_agent(repo, rs.local_path, rs.complexity)
            
            rs.patches = patch_res.get("patches", [])
            if rs.patches:
                _ok(repo, f"Generated & verified {len(rs.patches)} patch(es)")
            else:
                _ok(repo, "No complex files needed patching")
                
            rs.status = RepoStatus.PATCHED

        except Exception as exc:
            ps.error("PATCH", repo, traceback.format_exc())
            rs.add_warning(f"PatchAgent failed: {exc}")

    ps.transition("PATCH", "PREDICT")


# ─────────────────────────────────────────────
# STEP 4.6 — PREDICT (Ollama Bug/Crash Prediction)
# ─────────────────────────────────────────────

def _step_predict(ps: PipelineState) -> None:
    from bug_prediction_agent import run_bug_prediction

    _banner("PREDICT", "BugPredictionAgent — AI Analyzing Exact Source Code for Crashes")
    ps.current_step = Step.PREDICT

    for repo in ps.repos:
        rs = ps.repo_states[repo]

        if should_skip_repo(ps, repo) or not rs.complexity or not rs.local_path:
            _skip(repo, "no complexity data or local workspace")
            continue

        try:
            ps.info("PREDICT", repo, "Querying Ollama LLaMa3 for Exact Crash Predictions...")
            predict_res = run_bug_prediction(repo, rs.local_path, rs.complexity)
            
            rs.bug_predictions = predict_res
            if "error" not in predict_res and "predictions" in predict_res:
                _ok(repo, f"Generated real-time predictions for {predict_res.get('target_file')}")
            else:
                _skip(repo, predict_res.get("error", "No predictions needed"))
                
            rs.status = RepoStatus.PREDICTED

        except Exception as exc:
            ps.error("PREDICT", repo, traceback.format_exc())
            rs.add_warning(f"BugPredictionAgent failed: {exc}")

    ps.transition("PREDICT", "REPORT")


# ─────────────────────────────────────────────
# STEP 5 — REPORT (cross-repo, runs once)
# ─────────────────────────────────────────────

def _step_report(ps: PipelineState) -> str | None:
    from ceo_report_agent import ceo_report_agent

    _banner("REPORT", "CEOReportAgent — business narrative")
    ps.current_step = Step.REPORT

    payload = build_report_payload(ps)

    if not payload["risk_output"]:
        ps.warn("REPORT", None, "No risk output available — CEO report skipped")
        print("  [SKIP] CEO report — no scoreable repos")
        return None

    try:
        report = ceo_report_agent(
            risk_output       = payload["risk_output"],
            complexity_output = payload["complexity_output"],
            git_history_output= payload["git_history_output"],
        )
        ps.info("REPORT", None, "CEO report generated OK")
        print(f"  [OK ] CEO report written to reports/PEIP_EXECUTIVE_REPORT.md")
        return report

    except Exception as exc:
        handle(10, ps, "[CEO REPORT]", exc)   # Scenario 10: report generation failed
        ps.error("REPORT", None, traceback.format_exc())
        return None

    finally:
        ps.transition("REPORT", "DELIVER")


# ─────────────────────────────────────────────
# STEP 6 — DELIVER
# ─────────────────────────────────────────────

def _step_deliver(ps: PipelineState, ceo_report: str | None) -> dict:
    from dashboard_agent import render_dashboard

    _banner("DELIVER", "DashboardAgent — render to user")
    ps.current_step = Step.DELIVER

    final_output = build_deliver_payload(ps, ceo_report)

    # Persist full pipeline output
    with open("peip_pipeline_output.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, default=str)
    ps.info("DELIVER", None, "Pipeline output saved to peip_pipeline_output.json")

    # Build display records for DashboardAgent
    display_records = []
    for repo, rs in ps.repo_states.items():
        if rs.health:
            display_records.append(rs.health)

    if final_output and final_output.get("repos_analyzed"):
        render_dashboard(final_output)
    else:
        print("  [WARN] No health records to display.")

    if ps.all_warnings:
        print(f"\n[Orchestrator] {len(ps.all_warnings)} pipeline warning(s) logged:")
        for w in ps.all_warnings[:5]:
            print(f"  ! {w}")
        if len(ps.all_warnings) > 5:
            print(f"  ... and {len(ps.all_warnings) - 5} more — see peip_pipeline_output.json")

    ps.current_step = Step.DONE
    ps.delivery_done = True
    ps.transition("DELIVER", "DONE")

    return final_output


# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR — public entry point
# ─────────────────────────────────────────────

def run_pipeline(session_config: dict) -> dict:
    """
    The actual state machine orchestrator.
    Drives FETCH → MINE → ANALYZE → SCORE → REPORT → DELIVER per repo.
    Handles all 11 failure scenarios. Only stops on Scenario 11.
    Returns final_output dict for the caller.
    """
    ps = new_pipeline_state(session_config)

    print(f"\n[Orchestrator] Session {ps.session_id} — "
          f"{len(ps.repos)} repo(s) — window: {ps.analysis_window_days} days")

    wm = WorkspaceManager()
    
    try:
        # ── STEP 1: FETCH ─────────────────────────
        _step_fetch(ps, wm)
    
        # ── GATE: total wipeout check ─────────────
        if check_total_wipeout(ps):
            return {
                "session_id": ps.session_id,
                "error": "PIPELINE_HALTED",
                "reason": SCENARIOS[11]["user_msg"],
                "pipeline_log": ps.log,
            }
    
        # ── STEP 2: MINE ──────────────────────────
        _step_mine(ps)
    
        # ── STEP 3: ANALYZE ───────────────────────
        _step_analyze(ps)
    
        # ── STEP 4: SCORE ─────────────────────────
        _step_score(ps)
        
        # ── STEP 4.5: PATCH ───────────────────────
        _step_patch(ps)
        
        # ── STEP 4.6: PREDICT ─────────────────────
        _step_predict(ps)
    
        # ── STEP 5: REPORT ────────────────────────
        ceo_report = _step_report(ps)
        ps.ceo_report = ceo_report
    
        # ── STEP 6: DELIVER ───────────────────────
        final_output = _step_deliver(ps, ceo_report)
    
        print(f"\n[Orchestrator] Done — "
              f"{final_output.get('repos_analyzed', []).__len__()} analyzed, "
              f"{final_output.get('repos_skipped', []).__len__()} skipped, "
              f"{final_output.get('repos_failed', []).__len__()} failed.")
    
        return final_output
        
    finally:
        print("\n[Orchestrator] Pipeline finalized. Executing Cleanup...")
        wm.cleanup()


# ─────────────────────────────────────────────
# Smoke test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    demo_config = {
        "github_username":      "chaitu-png",
        "repos":                ["fintech-core-v2", "THIRD-PROJECT", "socialhive-api"],
        "token":                None,
        "analysis_window_days": 90,
        "scope":                "all_repos",
        "warnings":             [],
    }
    result = run_pipeline(demo_config)
    print("\nSession summary:", json.dumps(result.get("repos_analyzed"), indent=2))
