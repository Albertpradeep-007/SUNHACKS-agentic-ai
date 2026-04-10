"""
RiskAgent — Signal-Level Risk Classification

Receives GitHistoryAgent + ComplexityAgent outputs.
Classifies every component using individual research-validated thresholds.
No composite score bands — each flag is traceable to a published source.

90-day failure probability expressed as qualitative signal count:
  0 signals → "Low"
  1 signal  → "Moderate"
  2 signals → "High"
  3+        → "Critical — multiple validated risk signals simultaneously"

A percentage would imply a trained predictive model. We don't have one.
"""

SOURCES = {
    "CC_D":       "Radon/McCabe 1976 — CC >= 21 (Grade D+): high risk, act now.",
    "HOTSPOT":    "arXiv 2026 Hotspot Paper — top 20% churn + CC grade C or worse.",
    "BUS_HOTSPOT":"PyDriller (Spadini 2018) — bus factor = 1 on a hotspot file.",
    "MTTR":       "DORA 2024 'Low' band — bug MTTR > 7 days.",
    "CFR":        "DORA 2024 'Low' band — change failure rate > 15%.",
    "CC_C":       "Radon docs — CC 11-20 (Grade C): complex, testing becomes difficult.",
    "CHURN":      "Munson & Elbaum, IEEE 1998 — churn rate > 30% = validated fault surrogate.",
    "DEPLOY":     "DORA 2024 — deployment frequency < once per month.",
    "BUS_1":      "PyDriller (Spadini 2018) — bus factor = 1: sole non-minor contributor.",
    "TDI":        "TDI (cross-signal formula) — tdi > 3.5: refactor candidate.",
    "COUPLING":   "PyDriller ChangeSet — avg > 5 files per commit: tight coupling.",
    "OWNERSHIP":  "PyDriller ContributorsExperience — single owner > 80% of hotspot file.",
}


def _signal_count_to_probability(n: int) -> str:
    if n == 0: return "Low — no validated risk signals present."
    if n == 1: return "Moderate — 1 risk threshold crossed."
    if n == 2: return "High — 2 risk thresholds crossed."
    return f"Critical — {n} validated risk thresholds crossed simultaneously."


def _classify_file(filepath: str,
                   cc_grade: str,
                   cc_max: int,
                   tdi: float,
                   churn_rate: float,
                   is_hotspot: bool,
                   is_single_owner_hotspot: bool,
                   is_bus1: bool,
                   mttr_days: float | None,
                   cfr_pct: float | None,
                   deploy_freq: float | None) -> dict:
    """
    Classify a single file using signal-level rules.
    Returns component dict with signals, classification, failure_probability.
    """
    signals: list[dict] = []

    # ── CRITICAL signals ──────────────────────
    if cc_max >= 21:
        signals.append({
            "level":     "CRITICAL",
            "signal":    f"CC = {cc_max} (Grade {cc_grade}) — any function CC >= 21 is high risk.",
            "threshold": "CC >= 21 (Grade D+)",
            "source":    SOURCES["CC_D"]
        })

    if is_hotspot and cc_grade in ("C", "D", "E", "F"):
        signals.append({
            "level":     "CRITICAL",
            "signal":    f"HOTSPOT: in top 20% churn with CC Grade {cc_grade} — strongest defect predictor.",
            "threshold": "Top 20% churn + CC grade C or worse",
            "source":    SOURCES["HOTSPOT"]
        })

    if is_single_owner_hotspot:
        signals.append({
            "level":     "CRITICAL",
            "signal":    "Single contributor owns > 80% of this hotspot file.",
            "threshold": "Single owner > 80% on hotspot file",
            "source":    SOURCES["OWNERSHIP"]
        })

    if is_bus1 and is_hotspot:
        signals.append({
            "level":     "CRITICAL",
            "signal":    "Bus factor = 1 on a hotspot file — sole contributor + high churn.",
            "threshold": "Bus factor = 1 on hotspot file",
            "source":    SOURCES["BUS_HOTSPOT"]
        })

    if mttr_days is not None and mttr_days > 7:
        signals.append({
            "level":     "CRITICAL",
            "signal":    f"Bug MTTR = {mttr_days:.1f} days — exceeds 1-week threshold.",
            "threshold": "MTTR > 7 days (DORA 2024 Low)",
            "source":    SOURCES["MTTR"]
        })

    if cfr_pct is not None and cfr_pct > 0.15:
        signals.append({
            "level":     "CRITICAL",
            "signal":    f"Change failure rate {cfr_pct:.0%} — exceeds 15% threshold.",
            "threshold": "CFR > 15% (DORA 2024 Low)",
            "source":    SOURCES["CFR"]
        })

    is_critical = any(s["level"] == "CRITICAL" for s in signals)

    # ── AT RISK signals (only if not CRITICAL) ─
    if not is_critical:
        if cc_max >= 11:
            signals.append({
                "level":     "AT_RISK",
                "signal":    f"CC = {cc_max} (Grade {cc_grade}) — complex, testing becomes difficult.",
                "threshold": "CC 11-20 (Grade C)",
                "source":    SOURCES["CC_C"]
            })
        if churn_rate > 0.30:
            signals.append({
                "level":     "AT_RISK",
                "signal":    f"Churn rate {churn_rate:.0%} — validated fault surrogate.",
                "threshold": "> 30% LOC changed",
                "source":    SOURCES["CHURN"]
            })
        if deploy_freq is not None and deploy_freq < (1 / 30.0 * 7):  # < 1/month in weekly units
            signals.append({
                "level":     "AT_RISK",
                "signal":    f"Deployment frequency {deploy_freq:.2f}/week — less than once per month.",
                "threshold": "DF < once/month (DORA 2024 Low)",
                "source":    SOURCES["DEPLOY"]
            })
        if is_bus1 and not is_hotspot:
            signals.append({
                "level":     "AT_RISK",
                "signal":    "Bus factor = 1 — sole non-minor contributor.",
                "threshold": "Bus factor = 1",
                "source":    SOURCES["BUS_1"]
            })
        if tdi > 3.5:
            signals.append({
                "level":     "AT_RISK",
                "signal":    f"TDI = {tdi} — refactor candidate (threshold: 3.5).",
                "threshold": "TDI > 3.5",
                "source":    SOURCES["TDI"]
            })

    # ── Classification ────────────────────────
    crit_count   = sum(1 for s in signals if s["level"] == "CRITICAL")
    risk_count   = sum(1 for s in signals if s["level"] == "AT_RISK")
    total_signals = len(signals)

    if crit_count > 0:
        classification = "CRITICAL"
    elif risk_count > 0:
        classification = "AT RISK"
    elif cc_max <= 10 and churn_rate <= 0.30:
        classification = "STABLE"
    else:
        classification = "STABLE"

    plain = (
        f"This file has {cc_max} decision paths (Grade {cc_grade}), "
        f"a churn rate of {churn_rate:.0%}, and a TDI of {tdi}. "
    )
    if crit_count:
        plain += f"{crit_count} critical research threshold(s) crossed — act now."
    elif risk_count:
        plain += f"{risk_count} risk threshold(s) crossed — plan refactor within 30 days."
    else:
        plain += "No validated risk thresholds crossed."

    return {
        "file":                filepath,
        "classification":      classification,
        "signals_triggered":   signals,
        "signal_count":        total_signals,
        "failure_probability": _signal_count_to_probability(total_signals),
        "plain_english":       plain
    }


def risk_agent(repo_name: str,
               git_history: dict,
               complexity: dict | None) -> dict:
    """
    Cross-reference git_history and complexity to classify all components.
    Returns repo-level risk output conforming to spec.
    """
    hotspot_files         = set(git_history.get("hotspot_files", []))
    top20_churn           = set(git_history.get("top20_churn_files", []))
    single_owner_hotspots = set(git_history.get("single_owner_hotspot_files", []))
    bus1_files            = set(git_history.get("bus_factor_risk_files", []))
    deploy_freq_week      = git_history.get("commit_frequency_per_week")  # proxy
    mttr_days             = git_history.get("bug_mttr_days")
    cfr_pct               = None   # Not derivable from GitHub API without PR keyword scan

    components: list[dict] = []

    if complexity and complexity.get("files"):
        for filepath, fdata in complexity["files"].items():
            cc_grade   = fdata.get("cc_grade", "A")
            cc_max     = fdata.get("cc_max", 1)
            tdi        = fdata.get("tdi", 0.0)
            churn_rate = fdata.get("churn_rate", 0.0)

            is_hotspot        = filepath in hotspot_files or filepath in top20_churn
            is_single_owner   = filepath in single_owner_hotspots
            is_bus1           = filepath in bus1_files

            comp = _classify_file(
                filepath, cc_grade, cc_max, tdi, churn_rate,
                is_hotspot, is_single_owner, is_bus1,
                mttr_days, cfr_pct, deploy_freq_week
            )
            components.append(comp)
    else:
        # No Radon data — classify repo-level from git signals only
        components = [{
            "file":              "(no Python files found)",
            "classification":    "UNKNOWN",
            "signals_triggered": [],
            "signal_count":      0,
            "failure_probability": "Unknown — no complexity data available.",
            "plain_english":     "Radon complexity analysis could not run on this repo."
        }]

    # ── Repo-level classification ─────────────
    crit_comps = [c for c in components if c["classification"] == "CRITICAL"]
    risk_comps = [c for c in components if c["classification"] == "AT RISK"]

    if crit_comps:
        repo_class    = "CRITICAL"
        primary_comp  = sorted(crit_comps, key=lambda c: -c["signal_count"])[0]
    elif risk_comps:
        repo_class    = "AT RISK"
        primary_comp  = sorted(risk_comps, key=lambda c: -c["signal_count"])[0]
    else:
        repo_class    = "STABLE" if complexity else "UNKNOWN"
        primary_comp  = components[0] if components else {}

    primary_signal = (
        primary_comp.get("signals_triggered", [{}])[0].get("signal", "No critical signal")
        if primary_comp.get("signals_triggered") else "No critical signals detected."
    )

    return {
        "repo":              repo_name,
        "repo_classification": repo_class,
        "primary_signal":    primary_signal,
        "total_components":  len(components),
        "critical_count":    len(crit_comps),
        "at_risk_count":     len(risk_comps),
        "components":        components,
        "methodology_note":  (
            "Classification is signal-level, not composite-score-based. "
            "90-day failure probability is qualitative (signal count), not a percentage. "
            "A percentage would require a trained model on known-failing repos."
        )
    }
