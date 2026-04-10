from __future__ import annotations

import json
from datetime import datetime

from services.llm_client import chat_completion

CEO_PROMPT = """
You are a CTO writing a 1-page board-level report for a non-technical CEO.
Rules:
- NO technical jargon (no "cyclomatic complexity", no "churn rate")
- Translate risks into business consequences: lost revenue, outages, customer churn
- Give a cost-of-inaction figure in USD (assume $75/hr engineer, 8hr avg incident)
- Recommend a priority action list (max 4 items)
- Use confident, executive tone
- Format: markdown with sections: Executive Summary, Top Risks, Cost of Inaction, Recommended Actions

Inputs provided: repo name, risk predictions with remediation hours, test coverage trend proxies,
and deployment-frequency risk signals.
"""

ENG_HOURLY = 75
INCIDENT_HOURS = 8


def _fallback_report(repo_name: str, predictions: list[dict], health_scores: list[dict] | None = None) -> str:
    total_hours = sum(int(item.get("remediation_hours", 16)) for item in predictions)
    expected_incidents = sum(float(item.get("risk_probability", 0.0)) for item in predictions)
    incident_cost = expected_incidents * INCIDENT_HOURS * ENG_HOURLY
    weak_modules = [item for item in (health_scores or []) if item.get("tier") in {"red", "yellow"}][:5]

    lines = [
        "# Executive Summary",
        f"As of {datetime.utcnow().strftime('%Y-%m-%d')}, the repository **{repo_name}** has {len(predictions)} notable risk areas.",
        "The highest priority modules are likely to create service instability and avoidable support incidents unless addressed in this quarter.",
        "",
        "# Top Risks",
    ]

    if predictions:
        for item in predictions[:5]:
            lines.append(
                f"- **{item.get('module', 'unknown')}**: {item.get('urgency', 'medium')} urgency, "
                f"~{item.get('remediation_hours', 16)} hours, likely impact: {item.get('predicted_failure_type', 'instability')}."
            )
    else:
        lines.append("- No immediate high-risk modules were detected.")

        if weak_modules:
            lines.extend(["", "# Risk Evidence"])
            for item in weak_modules:
                lines.append(
                    f"- **{item.get('module', 'unknown')}**: score {item.get('score', 'n/a')}, "
                    f"bug density {item.get('bug_density', 0)}, test risk {item.get('test_risk', 0)}."
                )

    lines.extend(
        [
            "",
            "# Cost of Inaction",
            f"Estimated incident exposure: **${incident_cost:,.0f}** in engineering effort, "
            f"plus approximately **{total_hours} remediation hours** if deferred.",
            "",
            "# Recommended Actions",
            "1. Assign one owner per high-risk module and commit to a 2-week stabilization sprint.",
            "2. Prioritize bug-prone modules in release planning before new feature work.",
            "3. Add fast regression tests for top failure paths and enforce them in CI.",
            "4. Re-run this analysis in 30 days to verify risk reduction trend.",
        ]
    )
    return "\n".join(lines)


def generate_report(repo_name: str, predictions: list[dict], health_scores: list[dict] | None = None) -> str:
    total_hours = sum(int(item.get("remediation_hours", 16)) for item in predictions)
    expected_incidents = sum(float(item.get("risk_probability", 0.0)) for item in predictions)
    incident_cost = expected_incidents * INCIDENT_HOURS * ENG_HOURLY
    context = {
        "repo": repo_name,
        "total_remediation_hours": total_hours,
        "estimated_incident_cost_usd": incident_cost,
        "risks": predictions,
        "weakest_modules": (health_scores or [])[:8],
    }
    response = chat_completion(
        system_prompt=CEO_PROMPT,
        user_prompt=json.dumps(context, indent=2),
        temperature=0.4,
    )
    if not response:
        return _fallback_report(repo_name, predictions, health_scores)
    return response
