"""
ComplexityAgent v2 — Radon CC / MI / RAW metrics

Runs Radon CLI on cloned repos. Uses Radon's published grade scales only.
Computes Technical Debt Index (TDI) as cross-signal metric combining
CC grade, MI grade, and churn rate from GitHistoryAgent.

Grades:
  CC: A=1-5, B=6-10, C=11-20, D=21-30, E=31-40, F=41+  [Radon/McCabe1976]
  MI: A>=20, B=10-19, C<10                                [Radon/Coleman1994]

TDI formula (cross-signal):
  tdi = (cc_grade_num * 0.6) + (mi_grade_num * 0.2) + (churn_rate * 0.2)
  tdi > 3.5 → refactor candidate
  tdi > 5.0 → critical, block new features

Van Deursen 2014 caveat: MI grade C alone is NOT sufficient for CRITICAL.
Always pair MI with CC grade.
"""

import os
import json
import subprocess
import tempfile
import shutil


# ─────────────────────────────────────────────
# Grade lookups
# ─────────────────────────────────────────────

def _cc_grade(cc: int) -> tuple[str, int, str]:
    """Returns (letter, numeric, plain_english)."""
    if cc <= 5:  return "A", 1, "Simple, clean. Well-structured code."
    if cc <= 10: return "B", 2, "Acceptable. Worth monitoring."
    if cc <= 20: return "C", 3, "Complex. Testing becomes difficult. Flag for refactor planning."
    if cc <= 30: return "D", 4, "Very complex. High defect probability."
    if cc <= 40: return "E", 5, "Near-untestable. Any change is high risk."
    return "F", 6, "Severe — do not add features until fixed."


def _mi_grade(mi: float) -> tuple[str, int]:
    if mi >= 20: return "A", 1
    if mi >= 10: return "B", 2
    return "C", 3


def _tdi_status(tdi: float) -> str:
    if tdi > 5.0: return "CRITICAL — block new features on this file."
    if tdi > 3.5: return "Refactor candidate."
    return "Stable."


# ─────────────────────────────────────────────
# Radon runner
# ─────────────────────────────────────────────

def _run_radon(args: str, cwd: str) -> dict | list:
    """Run radon CLI, parse JSON output. Returns {} on failure."""
    cmd = f"python -m radon {args}"
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=120
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass
    return {}


# ─────────────────────────────────────────────
# Repo cloning helper
# ─────────────────────────────────────────────

def _clone_repo(github_username: str, repo_name: str,
                token: str | None) -> str | None:
    """
    Clone repo to a temp directory. Returns path or None on failure.
    Uses HTTPS with token if provided.
    """
    target = os.path.join("peip_repos", repo_name)
    if os.path.isdir(target):
        return target  # already cloned

    os.makedirs("peip_repos", exist_ok=True)

    if token:
        url = f"https://{token}@github.com/{github_username}/{repo_name}.git"
    else:
        url = f"https://github.com/{github_username}/{repo_name}.git"

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "500", url, target],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0:
            return target
        print(f"    [ComplexityAgent] Clone failed for {repo_name}: {result.stderr[:200]}")
        return None
    except Exception as e:
        print(f"    [ComplexityAgent] Clone error for {repo_name}: {e}")
        return None


# ─────────────────────────────────────────────
# Main agent
# ─────────────────────────────────────────────

def complexity_agent(repo_name: str,
                     github_username: str,
                     token: str | None,
                     git_history: dict,
                     local_repo_path: str = None) -> dict | None:
    """
    Run Radon CC/MI/RAW on the already cloned local repo, compute TDI.
    Returns structured dict or None if no Python files found.
    """
    print(f"  [ComplexityAgent] {repo_name}")

    if local_repo_path and os.path.exists(local_repo_path):
        repo_path = local_repo_path
    else:
        # Fall back to internal clone if not provided by Orchestrator
        repo_path = _clone_repo(github_username, repo_name, token)
        if not repo_path:
            return None

    # ── Run Radon ──────────────────────────────
    cc_data  = _run_radon("cc . -s -j", repo_path)
    mi_data  = _run_radon("mi . -s -j", repo_path)
    raw_data = _run_radon("raw . -s -j", repo_path)

    if not cc_data:
        print(f"    [ComplexityAgent] No Python files found in {repo_name}")
        return None

    # Build churn_rate lookup from git_history
    churn_raw = git_history.get("file_churn_raw", {})
    file_ar   = git_history.get("file_churn_added_removed", {})

    # Estimate total LOC per file for churn rate normalization
    def _churn_rate(filepath: str) -> float:
        raw = raw_data.get(filepath, {})
        loc = raw.get("loc", 0) if isinstance(raw, dict) else 0
        if loc <= 0:
            return 0.0
        ar = file_ar.get(filepath)
        if isinstance(ar, (list, tuple)) and len(ar) == 2:
            added, removed = ar
            return min((added + removed) / max(loc, 1), 1.0)
        raw_churn = churn_raw.get(filepath, 0)
        return min(raw_churn / max(loc, 1), 1.0)

    per_file: dict = {}
    max_cc_global  = 0
    highest_tdi_file = None
    highest_tdi_val  = 0.0
    highest_cc_fn    = None

    for filepath, blocks in cc_data.items():
        if not isinstance(blocks, list) or not blocks:
            continue

        # Max CC across functions (strictest signal per spec)
        fn_ccs = [(b.get("name", "?"), b.get("complexity", 1)) for b in blocks]
        max_fn_name, max_cc = max(fn_ccs, key=lambda x: x[1])

        cc_letter, cc_num, cc_msg = _cc_grade(max_cc)

        if max_cc > max_cc_global:
            max_cc_global = max_cc
            highest_cc_fn = {
                "name": max_fn_name, "cc": max_cc, "file": filepath
            }

        # MI
        mi_info  = mi_data.get(filepath, {})
        mi_val   = mi_info.get("mi", 100) if isinstance(mi_info, dict) else 100
        mi_letter, mi_num = _mi_grade(mi_val)

        # Van Deursen caveat: MI grade C alone is not enough — pair with CC
        mi_risk = (mi_letter == "C" and cc_letter not in ("A",))

        # RAW
        raw_info = raw_data.get(filepath, {})
        loc      = raw_info.get("loc", 0) if isinstance(raw_info, dict) else 0
        comments = raw_info.get("comments", 0) if isinstance(raw_info, dict) else 0
        comment_ratio = round(comments / max(loc, 1), 3)

        # Churn rate
        cr = _churn_rate(filepath)

        # TDI
        tdi = round((cc_num * 0.6) + (mi_num * 0.2) + (cr * 0.2), 2)
        if tdi > highest_tdi_val:
            highest_tdi_val  = tdi
            highest_tdi_file = filepath

        # Flags
        flags = []
        if cc_letter in ("C", "D", "E", "F"):
            flags.append("high_complexity")
        if tdi > 5.0:
            flags.append("tdi_critical")
        elif tdi > 3.5:
            flags.append("refactor_candidate")
        if comment_ratio < 0.05 and cc_num >= 3:
            flags.append("documentation_debt")
        if mi_risk:
            flags.append("mi_concern")

        # Plain English summary
        plain = (
            f"This file's most complex function has {max_cc} decision paths "
            f"(Grade {cc_letter} — {cc_msg}) "
            f"and a maintainability score of {round(mi_val, 1)} (Grade {mi_letter}). "
            f"Technical Debt Index: {tdi} — {_tdi_status(tdi)}"
        )

        per_file[filepath] = {
            "file":          filepath,
            "cc_grade":      cc_letter,
            "cc_max":        max_cc,
            "cc_max_fn":     max_fn_name,
            "mi_grade":      mi_letter,
            "mi_score":      round(mi_val, 1),
            "tdi":           tdi,
            "tdi_status":    _tdi_status(tdi),
            "comment_ratio": comment_ratio,
            "churn_rate":    round(cr, 3),
            "flags":         flags,
            "plain_english": plain
        }

    if not per_file:
        return None

    # Repo-level grade distribution
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    for f in per_file.values():
        g = f["cc_grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1
    total_files = len(per_file)
    pct_c_or_worse = round(
        sum(grade_counts[g] for g in ("C", "D", "E", "F")) / max(total_files, 1), 2
    )

    return {
        "repo":         repo_name,
        "files":        per_file,
        "repo_summary": {
            "total_python_files":   total_files,
            "grade_distribution":   grade_counts,
            "pct_grade_C_or_worse": pct_c_or_worse,
            "highest_tdi_file":     highest_tdi_file,
            "highest_tdi_value":    highest_tdi_val,
            "highest_cc_function":  highest_cc_fn
        }
    }
