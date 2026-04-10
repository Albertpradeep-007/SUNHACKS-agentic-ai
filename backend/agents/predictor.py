from __future__ import annotations

import json
import re

from services.llm_client import chat_completion

PREDICT_PROMPT = """
You are a senior engineering risk analyst.
Given module health scores and trends, identify:
1. Which modules will likely fail or cause incidents in 90 days
2. The probable business impact (outage, data loss, slow performance)
3. Estimated hours to remediate each

Input includes additional engineering signals:
- test_touch_ratio (0-1)
- test_coverage_trend (negative means worsening)
- deployment_frequency_per_commit (0-1)

Use these signals in your judgment and keep outputs conservative when data is sparse.

Return ONLY valid JSON: list of objects with keys:
module, risk_probability (0-1), predicted_failure_type, remediation_hours, urgency (high|medium|low), prediction_window_days
"""


def _strip_code_fences(content: str) -> str:
    matched = re.search(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if matched:
        return matched.group(1)
    return content.strip()


def _rule_based_predictions(health_scores: list[dict]) -> list[dict]:
    predictions = []
    risky = sorted((row for row in health_scores if row.get("tier") != "green"), key=lambda row: row.get("score", 100))
    for row in risky[:10]:
        score = float(row.get("score", 50.0))
        bug_density = float(row.get("bug_density", 0.0))
        complexity = float(row.get("complexity", 0.0))
        test_gap = 1.0 - float(row.get("test_touch_ratio", 0.0))
        deploy_pressure = float(row.get("deployment_frequency_per_commit", 0.0))

        decay_per_week = bug_density * 2.0 + complexity * 5.0 + test_gap * 2.0 + deploy_pressure * 1.5
        projected_90d = max(0.0, score - decay_per_week * 13.0)
        probability = round(min(0.95, (100.0 - projected_90d) / 100.0), 2)

        urgency = "high" if probability >= 0.75 else ("medium" if probability >= 0.45 else "low")
        if test_gap >= 0.7:
            failure_type = "regression due to weak test safety"
        elif deploy_pressure >= 0.4:
            failure_type = "release instability"
        elif complexity >= 0.6:
            failure_type = "outage"
        elif bug_density >= 0.2:
            failure_type = "performance regression"
        else:
            failure_type = "service instability"
        remediation_hours = int(8 + bug_density * 60 + complexity * 30 + test_gap * 20)

        predictions.append(
            {
                "module": row.get("module"),
                "risk_probability": probability,
                "predicted_failure_type": failure_type,
                "remediation_hours": remediation_hours,
                "urgency": urgency,
                "prediction_window_days": 90,
                "projected_score_90d": round(projected_90d, 1),
                "test_touch_ratio": round(max(0.0, min(1.0, 1.0 - test_gap)), 3),
                "deployment_frequency_per_commit": round(max(0.0, deploy_pressure), 3),
            }
        )
    return predictions


def _normalize_predictions(parsed: object, baseline: list[dict]) -> list[dict]:
    if not isinstance(parsed, list):
        return []

    baseline_by_module = {str(item.get("module")): item for item in baseline if item.get("module")}
    normalized: list[dict] = []

    for item in parsed:
        if not isinstance(item, dict):
            continue

        module = str(item.get("module") or "").strip()
        if not module:
            continue

        base = baseline_by_module.get(module, {})
        base_probability = float(base.get("risk_probability", 0.5))
        try:
            probability = float(item.get("risk_probability", base_probability))
        except (TypeError, ValueError):
            probability = base_probability
        # Keep LLM adjustments bounded around data-driven baseline estimates.
        probability = base_probability * 0.65 + probability * 0.35
        probability = round(max(0.0, min(probability, 0.95)), 2)

        base_remediation = int(base.get("remediation_hours", 24))
        try:
            remediation_hours = int(item.get("remediation_hours", base_remediation))
        except (TypeError, ValueError):
            remediation_hours = base_remediation
        remediation_hours = int(round(base_remediation * 0.7 + remediation_hours * 0.3))

        urgency = str(item.get("urgency", base.get("urgency", "medium"))).lower()
        if urgency not in {"high", "medium", "low"}:
            urgency = "medium"

        normalized_item = {
            "module": module,
            "risk_probability": probability,
            "predicted_failure_type": str(
                item.get("predicted_failure_type", base.get("predicted_failure_type", "service instability"))
            ),
            "remediation_hours": max(remediation_hours, 1),
            "urgency": urgency,
            "prediction_window_days": 90,
        }

        if "projected_score_90d" in base:
            normalized_item["projected_score_90d"] = base["projected_score_90d"]
        if "test_touch_ratio" in base:
            normalized_item["test_touch_ratio"] = base["test_touch_ratio"]
        if "deployment_frequency_per_commit" in base:
            normalized_item["deployment_frequency_per_commit"] = base["deployment_frequency_per_commit"]

        normalized.append(normalized_item)

    return normalized


def predict_risks(health_scores: list[dict]) -> list[dict]:
    baseline = _rule_based_predictions(health_scores)
    if not baseline:
        return baseline

    context = json.dumps(baseline, indent=2)
    response = chat_completion(
        system_prompt=PREDICT_PROMPT,
        user_prompt=f"Modules:\n{context}",
        temperature=0.2,
    )
    if not response:
        return baseline

    try:
        parsed = json.loads(_strip_code_fences(response))
        normalized = _normalize_predictions(parsed, baseline)
        if normalized:
            return normalized
    except Exception:
        pass
    return baseline
