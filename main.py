"""
PEIP — Predictive Engineering Intelligence Platform
Main Entrypoint

LAYER 1  → InputAgent     (input_agent.py)       — validate GitHub details
LAYER 2  → MasterAgent    (master_agent.py)
             ↳ GitHistoryAgent (git_history_agent.py)
             ↳ ComplexityAgent (complexity_agent2.py)
             ↳ RiskAgent       (risk_agent.py)
             ↳ CEOReportAgent  (ceo_report_agent2.py)
LAYER 3  → DashboardAgent (dashboard_agent.py)   — render final report

Usage:
    python main.py                    # full interactive pipeline
    python main.py --demo             # non-interactive using simulated profiles
    python main.py --live             # interactive + real GitHub + Radon pipeline
"""

import sys
import json
import argparse
import os

# Dynamically append modular engine folders to sys.path so agents/core/services resolve
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(BASE_DIR, "peip_engine")
sys.path.extend([
    os.path.join(ENGINE_DIR, "agents"),
    os.path.join(ENGINE_DIR, "core"),
    os.path.join(ENGINE_DIR, "services"),
])


# ─────────────────────────────────────────────
# Demo mode — uses peip_analytics.py profiles
# (no GitHub cloning, no Radon, instant output)
# ─────────────────────────────────────────────

DEMO_REPOS = [
    "fintech-core-v2",
    "scalechat-realtime",
    "socialhive-api",
    "PROJECT_1",
    "PROJECT_2",
    "THIRD-PROJECT",
]


def run_demo() -> None:
    from peip_analytics  import health_score_agent
    from dashboard_agent import render_dashboard

    print("\n[PEIP] Demo mode — using validated signal profiles (no GitHub cloning needed)")
    print("[PEIP] Intelligence Layer — evaluating signals...\n")

    results = [health_score_agent(repo) for repo in DEMO_REPOS]

    with open("peip_health_scores.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    render_dashboard(results)


# ─────────────────────────────────────────────
# Live mode — full 4-agent Intelligence Layer
# ─────────────────────────────────────────────

def run_live(session_config: dict) -> None:
    """
    Route through MasterAgent → 4 sub-agents → DashboardAgent.
    MasterAgent returns a unified final_output dict.
    DashboardAgent receives the risk_flags list for rendering.
    """
    from master_agent    import run_pipeline
    from dashboard_agent import render_dashboard

    final_output = run_pipeline(session_config)

    # Persist full pipeline output
    with open("peip_pipeline_output.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, default=str)

    # DashboardAgent expects a list of repo health dicts
    # We convert risk_flags output to the format DashboardAgent understands
    risk_flags   = final_output.get("risk_flags", {})
    git_history  = final_output.get("git_history", {})
    complexity   = final_output.get("complexity", {})

    # Build unified display records (one per repo) for DashboardAgent
    display_records = []
    for repo, risk in risk_flags.items():
        all_flags = []
        for comp in risk.get("components", []):
            all_flags.extend(comp.get("signals_triggered", []))

        # Map to dashboard_agent expected schema
        git = git_history.get(repo, {})
        cmplx = complexity.get(repo) or {}
        files = cmplx.get("files", {})

        # Pick worst CC from complexity
        cc_vals = [(f.get("cc_grade","A"), f.get("cc_max",1))
                   for f in files.values()] if files else [("A", 1)]
        worst_cc_grade = max(cc_vals, key=lambda x: "ABCDEF".index(x[0]))[0]
        worst_cc_val   = max(cc_vals, key=lambda x: x[1])[1]

        record = {
            "repository":           repo,
            "classification":       risk.get("repo_classification", "UNKNOWN"),
            "display":              (
                f"{risk.get('repo_classification','?')} — "
                f"{risk.get('primary_signal', '')}"
            ),
            "classification_reason": risk.get("primary_signal", ""),
            "flags_triggered":       all_flags,
            "signals": {
                "cyclomatic_complexity": {
                    "value":  worst_cc_val,
                    "grade":  worst_cc_grade,
                    "source": "McCabe 1976, IEEE + Radon docs"
                },
                "maintainability_index": {
                    "value": None,
                    "grade": None,
                    "source": "Coleman et al. 1994"
                },
                "code_churn": {
                    "rate":  git.get("churn_trend", "unknown"),
                    "label": git.get("churn_trend", "unknown"),
                    "source": "Munson & Elbaum 1998"
                },
                "bus_factor": {
                    "value":  len(git.get("bus_factor_risk_files", [])),
                    "source": "Spadini et al. 2018"
                },
                "hotspot": {
                    "triggered": bool(git.get("hotspot_files")),
                    "source": "arXiv 2026" if git.get("hotspot_files") else None
                },
                "dora": {
                    "breakdown": {},
                    "archetype": "See risk_flags for detail",
                    "source": "DORA 2024/2025"
                }
            }
        }
        display_records.append(record)

    if display_records:
        render_dashboard(final_output)

    if final_output.get("pipeline_warnings"):
        print("\n[PEIP] Pipeline warnings:")
        for w in final_output["pipeline_warnings"]:
            print(f"  ! {w}")

    print("\n[PEIP] Full pipeline data: peip_pipeline_output.json")
    if final_output.get("ceo_report"):
        print("[PEIP] CEO report: reports/PEIP_EXECUTIVE_REPORT.md")


# ─────────────────────────────────────────────
# CLI entrypoint
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PEIP — Predictive Engineering Intelligence Platform"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run non-interactively with validated signal profiles (no GitHub token needed)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Interactive mode: prompt for GitHub URL + token, run full 4-agent pipeline"
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()

    elif args.live:
        try:
            from input_agent  import run_input_agent
            from orchestrator import run_pipeline as _orchestrate
            session_config = run_input_agent()
            # Route through real state machine orchestrator
            _orchestrate(session_config)
        except KeyboardInterrupt:
            print("\n[PEIP] Cancelled.")
            sys.exit(0)

    else:
        # Default: demo mode for quick validation
        print("[PEIP] No flag specified. Running demo mode.")
        print("       Use --live for the full interactive pipeline with GitHub + Radon.\n")
        run_demo()
