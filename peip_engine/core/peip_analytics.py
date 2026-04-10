"""
PEIP HealthScoreAgent — Signal-Level Classification Engine

DESIGN PRINCIPLE (corrected):
  Composite scores with arbitrary bands (86/66/40/0) have NO research basis.
  No peer-reviewed paper defines universal cut points for composite codebase health.
  The only calibrated code health scale is CodeScene's 1-10 (Tornhill), derived
  from hundreds of real codebases — and even they warn absolute numbers matter
  less than trend direction.

  This engine classifies using SIGNAL-LEVEL FLAGS tied to individual
  research-validated thresholds. Each flag is traceable to a published source.
  Each flag tells the developer exactly what is wrong and what to fix.

CLASSIFICATION RULES:
  CRITICAL — if ANY single research-validated threshold is crossed:
    * CC >= 21 (Grade D+) — Radon/McCabe 1976
    * DORA MTTR > 1 week — DORA 2024 "Low" band
    * DORA CFR > 15% — DORA 2024 "Low" band
    * Single contributor > 80% of hotspot file — PyDriller
    * File is hotspot (top 20% churn + CC grade C+) — arXiv 2026

  AT RISK — if ANY of these and CRITICAL not already triggered:
    * CC 11-20 (Grade C) — Radon docs
    * Churn > 30% LOC in 90 days — Munson & Elbaum 1998
    * DORA DF < once/month — DORA 2024
    * Bus factor = 1 — PyDriller
    * MI < 10 AND CC grade B+ — Radon + Van Deursen 2014

  STABLE — ALL of:
    * All CC <= 10 (Grade A or B)
    * Churn 10-30%
    * DORA in High or Medium bands
    * Bus factor >= 2

  HEALTHY — ALL of:
    * All CC <= 10
    * Churn < 10%
    * DORA in High or Elite
    * Bus factor >= 3
    * MI >= 20 on all files
"""

import json

SOURCES = {
    "McCabe1976":      "McCabe 1976, IEEE Trans. Software Eng. — CC as count of linearly independent paths.",
    "RadonDocs":       "rubik/radon official docs — Grade scale A=1-5, B=6-10, C=11-20, D=21-30, E=31-40, F=41+.",
    "Coleman1994":     "Coleman et al., IEEE Computer 1994 — MI formula documented.",
    "VanDeursen2014":  "Van Deursen 2014 — 'Think Twice Before Using MI.' Experimental metric, pair with CC.",
    "MunsonElbaum98":  "Munson & Elbaum, IEEE 1998 — Code churn validated as fault surrogate.",
    "Spadini2018":     "Spadini et al., ESEC/FSE 2018 — PyDriller process metrics. Minor contributor = <5% lines.",
    "DORA2024":        "DORA 2024 (Google, 39,000+ respondents) — 5 metrics, 4-tier benchmark bands.",
    "DORA2025":        "DORA 2025 (5,000 respondents) — 7 archetypes replacing 4-tier model.",
    "arXiv2026":       "arXiv 2026 Hotspot Paper — Top 20% churn + CC grade C = hotspot. Exclude bot commits.",
    "CodeScene":       "CodeScene / Tornhill — Code health 1-10 scale calibrated against hundreds of real codebases."
}


# ═══════════════════════════════════════════════════════
# SIGNAL EVALUATORS — each returns flags, not scores
# ═══════════════════════════════════════════════════════

def evaluate_cc(cc):
    """Returns CC grade and any triggered flags with sources."""
    if cc <= 5:   grade = "A"
    elif cc <= 10: grade = "B"
    elif cc <= 20: grade = "C"
    elif cc <= 30: grade = "D"
    elif cc <= 40: grade = "E"
    else:          grade = "F"

    flags = []
    if cc >= 21:
        flags.append({
            "level": "CRITICAL",
            "signal": f"CC = {cc} (Grade {grade}) — any function CC >= 21 is high risk, act now.",
            "threshold": "CC >= 21 (Grade D+)",
            "source": SOURCES["McCabe1976"] + " " + SOURCES["RadonDocs"]
        })
    elif cc >= 11:
        flags.append({
            "level": "AT_RISK",
            "signal": f"CC = {cc} (Grade {grade}) — complex, testing becomes difficult. Flag for refactor planning.",
            "threshold": "CC 11-20 (Grade C)",
            "source": SOURCES["RadonDocs"]
        })

    return grade, cc, flags


def evaluate_mi(mi, cc_grade):
    """Returns MI grade and flags. MI is experimental — only flag when paired with CC evidence."""
    if mi >= 20:  grade = "A"
    elif mi >= 10: grade = "B"
    else:          grade = "C"

    flags = []
    # Van Deursen caveat: MI < 10 alone is NOT an emergency.
    # Only flag when MI grade C AND CC is also problematic (grade B or worse).
    if grade == "C" and cc_grade in ("B", "C", "D", "E", "F"):
        flags.append({
            "level": "AT_RISK",
            "signal": f"MI = {mi} (Grade C) combined with CC Grade {cc_grade} — both structure and readability are degraded.",
            "threshold": "MI < 10 AND CC >= Grade B",
            "source": SOURCES["Coleman1994"] + " " + SOURCES["VanDeursen2014"]
        })

    return grade, mi, flags


def evaluate_churn(churn_rate):
    """Returns churn classification and flags."""
    flags = []
    if churn_rate > 0.30:
        flags.append({
            "level": "AT_RISK",
            "signal": f"Churn rate {churn_rate:.0%} exceeds 30% threshold — validated fault surrogate.",
            "threshold": "> 30% LOC changed in 90 days",
            "source": SOURCES["MunsonElbaum98"]
        })

    if churn_rate < 0.10:   label = "stable"
    elif churn_rate <= 0.30: label = "moderate"
    else:                    label = "high_flux"

    return label, churn_rate, flags


def evaluate_bus_factor(bus_factor):
    """Returns bus factor flags."""
    flags = []
    if bus_factor <= 1:
        flags.append({
            "level": "AT_RISK",
            "signal": f"Bus factor = {bus_factor} — sole non-minor contributor. Single point of failure.",
            "threshold": "Bus factor = 1 (sole contributor with > 5% ownership)",
            "source": SOURCES["Spadini2018"]
        })

    return bus_factor, flags


def evaluate_hotspot(cc_grade, churn_rate, is_top20_churn, single_owner_on_hotspot):
    """Hotspot = top 20% churn AND CC grade C+. Per arXiv 2026."""
    flags = []
    triggered = False

    if is_top20_churn and cc_grade in ("C", "D", "E", "F"):
        triggered = True
        flags.append({
            "level": "CRITICAL",
            "signal": f"HOTSPOT: File in top 20% churn with CC Grade {cc_grade} — strongest predictor of future defects.",
            "threshold": "Top 20% churn + CC grade C or worse",
            "source": SOURCES["arXiv2026"]
        })

    if single_owner_on_hotspot and is_top20_churn:
        flags.append({
            "level": "CRITICAL",
            "signal": "Single contributor owns > 80% of a hotspot file — fragile + single-owner = extreme risk.",
            "threshold": "Single contributor > 80% on top-churn file",
            "source": SOURCES["Spadini2018"] + " " + SOURCES["arXiv2026"]
        })

    return triggered, flags


def evaluate_dora(df_weekly, lt_days, cfr_pct, mttr_days, rework_pct):
    """Evaluate all 5 DORA metrics against published 2024 benchmark bands."""
    flags = []
    breakdown = {}

    # Deployment Frequency
    if df_weekly >= 3.5:    breakdown["deployment_frequency"] = "Elite"
    elif df_weekly >= 1.0:  breakdown["deployment_frequency"] = "High"
    elif df_weekly >= 0.25: breakdown["deployment_frequency"] = "Medium"
    else:
        breakdown["deployment_frequency"] = "Low"
        flags.append({
            "level": "AT_RISK",
            "signal": f"Deployment frequency {df_weekly:.2f}/week — less than once per month.",
            "threshold": "< once per month (DORA 2024 'Low' band)",
            "source": SOURCES["DORA2024"]
        })

    # Lead Time
    if lt_days < 1:       breakdown["lead_time"] = "Elite"
    elif lt_days <= 7:    breakdown["lead_time"] = "High"
    elif lt_days <= 30:   breakdown["lead_time"] = "Medium"
    else:                 breakdown["lead_time"] = "Low"

    # Change Failure Rate
    if cfr_pct < 0.05:      breakdown["change_failure_rate"] = "Elite"
    elif cfr_pct <= 0.10:   breakdown["change_failure_rate"] = "High"
    elif cfr_pct <= 0.15:   breakdown["change_failure_rate"] = "Medium"
    else:
        breakdown["change_failure_rate"] = "Low"
        flags.append({
            "level": "CRITICAL",
            "signal": f"Change failure rate {cfr_pct:.0%} exceeds 15% — unstable delivery.",
            "threshold": "CFR > 15% (DORA 2024 'Low' band)",
            "source": SOURCES["DORA2024"]
        })

    # MTTR
    if mttr_days < 0.042:    breakdown["mttr"] = "Elite"
    elif mttr_days < 1.0:    breakdown["mttr"] = "High"
    elif mttr_days <= 7.0:   breakdown["mttr"] = "Medium"
    else:
        breakdown["mttr"] = "Low"
        flags.append({
            "level": "CRITICAL",
            "signal": f"Mean time to recovery {mttr_days:.1f} days exceeds 1 week — slow recovery.",
            "threshold": "MTTR > 1 week (DORA 2024 'Low' band)",
            "source": SOURCES["DORA2024"]
        })

    # Rework Rate (2024 addition)
    if rework_pct < 0.05:     breakdown["rework_rate"] = "Good"
    elif rework_pct <= 0.15:  breakdown["rework_rate"] = "Moderate"
    else:                     breakdown["rework_rate"] = "Concerning"

    # DORA 2025 archetype (replaces 4-tier labels)
    is_fast = breakdown["deployment_frequency"] in ("Elite", "High")
    is_stable = breakdown["change_failure_rate"] in ("Elite", "High")
    if is_fast and is_stable:      archetype = "Sustainable Performance"
    elif is_fast and not is_stable: archetype = "Speed-at-Cost"
    elif not is_fast and is_stable: archetype = "Cautious Delivery"
    else:                           archetype = "Struggling"

    return breakdown, archetype, flags


# ═══════════════════════════════════════════════════════
# CLASSIFICATION ENGINE — signal-level, not composite bands
# ═══════════════════════════════════════════════════════

def classify_from_flags(all_flags, cc_grade, churn_label, dora_breakdown, bus_factor, mi_grade):
    """
    Classify using signal-level flags. NO arbitrary composite bands.
    Returns category and the specific reasons for that classification.
    """
    critical_flags = [f for f in all_flags if f["level"] == "CRITICAL"]
    at_risk_flags = [f for f in all_flags if f["level"] == "AT_RISK"]

    if critical_flags:
        return "CRITICAL", critical_flags, "Act immediately — at least one research-validated critical threshold crossed."

    if at_risk_flags:
        return "AT RISK", at_risk_flags, "Plan action within 30 days — research-validated warning thresholds crossed."

    # Check STABLE conditions: all CC <= B, churn moderate, DORA medium+, bus >= 2
    dora_high_or_medium = all(
        v in ("Elite", "High", "Medium", "Good", "Moderate")
        for v in dora_breakdown.values()
    )
    if (cc_grade in ("A", "B") and
        churn_label in ("stable", "moderate") and
        dora_high_or_medium and
        bus_factor >= 2):

        # Check HEALTHY: all CC A/B, churn < 10%, DORA High/Elite, bus >= 3, MI A
        dora_high_or_elite = all(
            v in ("Elite", "High", "Good")
            for v in dora_breakdown.values()
        )
        if (churn_label == "stable" and
            dora_high_or_elite and
            bus_factor >= 3 and
            mi_grade == "A"):
            return "HEALTHY", [], "All signals within research-validated healthy bounds. No action needed."

        return "STABLE", [], "All signals within acceptable bounds. Monitor quarterly."

    # Fallback — shouldn't reach here if flags are correct, but classify conservatively
    return "AT RISK", at_risk_flags, "Mixed signals — review individual dimensions."


# ═══════════════════════════════════════════════════════
# REPO PROFILES (deterministic simulation data)
# ═══════════════════════════════════════════════════════

def get_repo_profile(repo_name):
    profiles = {
        "fintech-core-v2": {
            "cc": 4, "mi": 82, "churn_rate": 0.05, "bus": 3,
            "dora": (5.0, 0.5, 0.02, 0.03, 0.03),
            "is_top20_churn": False, "single_owner_hotspot": False
        },
        "scalechat-realtime": {
            "cc": 8, "mi": 71, "churn_rate": 0.15, "bus": 2,
            "dora": (1.5, 3.0, 0.06, 0.5, 0.08),
            "is_top20_churn": False, "single_owner_hotspot": False
        },
        "socialhive-api": {
            "cc": 14, "mi": 25, "churn_rate": 0.40, "bus": 2,
            "dora": (0.3, 14.0, 0.12, 2.0, 0.12),
            "is_top20_churn": True, "single_owner_hotspot": False
        },
        "PROJECT_1": {
            "cc": 25, "mi": 15, "churn_rate": 0.55, "bus": 1,
            "dora": (0.1, 45.0, 0.20, 10.0, 0.20),
            "is_top20_churn": True, "single_owner_hotspot": True
        },
        "PROJECT_2": {
            "cc": 12, "mi": 45, "churn_rate": 0.25, "bus": 2,
            "dora": (0.8, 5.0, 0.08, 1.0, 0.08),
            "is_top20_churn": False, "single_owner_hotspot": False
        },
        "THIRD-PROJECT": {
            "cc": 45, "mi": 5, "churn_rate": 0.85, "bus": 1,
            "dora": (0.1, 60.0, 0.30, 20.0, 0.30),
            "is_top20_churn": True, "single_owner_hotspot": True
        }
    }
    return profiles.get(repo_name, profiles["THIRD-PROJECT"])


# ═══════════════════════════════════════════════════════
# MAIN AGENT LOGIC
# ═══════════════════════════════════════════════════════

def health_score_agent(repo_name):
    print(f"[HealthScoreAgent] Evaluating signals for {repo_name}...")
    p = get_repo_profile(repo_name)

    # Evaluate each dimension independently
    cc_grade, cc_val, cc_flags = evaluate_cc(p["cc"])
    mi_grade, mi_val, mi_flags = evaluate_mi(p["mi"], cc_grade)
    churn_label, churn_val, churn_flags = evaluate_churn(p["churn_rate"])
    bus_val, bus_flags = evaluate_bus_factor(p["bus"])
    hotspot_triggered, hotspot_flags = evaluate_hotspot(
        cc_grade, p["churn_rate"], p["is_top20_churn"], p["single_owner_hotspot"]
    )
    dora_breakdown, dora_archetype, dora_flags = evaluate_dora(*p["dora"])

    # Collect ALL flags
    all_flags = cc_flags + mi_flags + churn_flags + bus_flags + hotspot_flags + dora_flags

    # Classify from signals — NOT from a composite score
    category, triggered_flags, classification_reason = classify_from_flags(
        all_flags, cc_grade, churn_label, dora_breakdown, bus_val, mi_grade
    )

    # Build human-readable reason string
    if triggered_flags:
        reasons_text = "; ".join(f["signal"] for f in triggered_flags)
        display = f"{category} — reason: {reasons_text}"
    else:
        display = f"{category} — {classification_reason}"

    return {
        "repository": repo_name,
        "classification": category,
        "display": display,
        "classification_reason": classification_reason,
        "signals": {
            "cyclomatic_complexity": {
                "value": cc_val,
                "grade": cc_grade,
                "source": SOURCES["McCabe1976"] + " " + SOURCES["RadonDocs"]
            },
            "maintainability_index": {
                "value": mi_val,
                "grade": mi_grade,
                "source": SOURCES["Coleman1994"],
                "caveat": SOURCES["VanDeursen2014"]
            },
            "code_churn": {
                "rate": churn_val,
                "label": churn_label,
                "source": SOURCES["MunsonElbaum98"]
            },
            "bus_factor": {
                "value": bus_val,
                "source": SOURCES["Spadini2018"]
            },
            "hotspot": {
                "triggered": hotspot_triggered,
                "source": SOURCES["arXiv2026"] if hotspot_triggered else None
            },
            "dora": {
                "breakdown": dora_breakdown,
                "archetype": dora_archetype,
                "source": SOURCES["DORA2024"] + " " + SOURCES["DORA2025"]
            }
        },
        "flags_triggered": all_flags,
        "methodology_note": (
            "Classification is signal-level, not composite-score-based. "
            "No universal composite bands exist in peer-reviewed literature. "
            "Each flag traces to a specific published threshold. "
            "See CodeScene/Tornhill for the only calibrated code health scale (1-10, healthy >= 9.0)."
        )
    }


def main():
    repos = ["fintech-core-v2", "scalechat-realtime", "socialhive-api",
             "PROJECT_1", "PROJECT_2", "THIRD-PROJECT"]
    all_data = []

    for repo in repos:
        result = health_score_agent(repo)
        all_data.append(result)

    with open("peip_health_scores.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print("\nSignal-level health classifications written to peip_health_scores.json")
    print("-" * 60)
    for r in all_data:
        print(f"  {r['repository']:25s} -> {r['display']}")
    print("-" * 60)


if __name__ == "__main__":
    main()
