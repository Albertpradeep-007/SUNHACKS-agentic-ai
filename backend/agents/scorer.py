from __future__ import annotations

from datetime import datetime, timezone

from services.radon_runner import get_radon_scores

WEIGHTS = {
    "churn": 0.22,
    "bug_density": 0.24,
    "complexity": 0.16,
    "age": 0.10,
    "test": 0.12,
    "deploy": 0.08,
    "author": 0.08,
}


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _age_risk(last_modified: str | None) -> float:
    timestamp = _parse_iso_datetime(last_modified)
    if not timestamp:
        return 0.5
    now = datetime.now(timezone.utc)
    days_since = max((now - timestamp).days, 0)
    # Recently modified files are usually less stable in the short term.
    return 1.0 - min(days_since / 90.0, 1.0)


def _file_extension(path: str) -> str:
    normalized = (path or "").replace("\\", "/")
    filename = normalized.rsplit("/", 1)[-1]
    if "." not in filename:
        return ""
    return filename[filename.rfind(".") :].lower()


def _non_python_complexity_proxy(metric: dict, churn_norm: float, bug_density: float) -> float:
    deploy_pressure = max(0.0, min(float(metric.get("deployment_frequency_per_commit", 0.0)), 1.0))
    author_count = max(int(metric.get("authors", 1)), 1)
    single_author_risk = 1.0 - min(author_count / 3.0, 1.0)
    # Approximate structural risk when language-specific static analysis is unavailable.
    return min(0.30 + churn_norm * 0.35 + bug_density * 0.25 + deploy_pressure * 0.1 + single_author_risk * 0.1, 1.0)


def compute_health_scores(raw_metrics: list[dict], repo_path: str) -> list[dict]:
    target_paths = [str(item.get("module", "")) for item in raw_metrics if item.get("module")]
    radon_scores = get_radon_scores(repo_path, target_paths=target_paths)
    max_churn = max((item.get("churn", 0) for item in raw_metrics), default=1)
    scored: list[dict] = []

    for metric in raw_metrics:
        path = metric.get("module", "")
        radon = radon_scores.get(path, {"cc": 5.0, "mi": 70.0})

        commit_count = max(float(metric.get("commit_count", 0)), 1.0)
        bug_fix_count = max(float(metric.get("bug_fix_count", 0)), 0.0)
        sample_confidence = min(commit_count / 5.0, 1.0)

        churn_norm = float(metric.get("churn", 0)) / max(max_churn, 1)
        bug_density = (bug_fix_count / max(commit_count + 2.0, 1.0)) * (0.5 + 0.5 * sample_confidence)
        ext = _file_extension(path)
        if ext == ".py" and path in radon_scores:
            cc_norm = min(float(radon.get("cc", 0.0)) / 20.0, 1.0)
            mi_norm = 1.0 - min(max(float(radon.get("mi", 100.0)), 0.0), 100.0) / 100.0
            complexity = (cc_norm + mi_norm) / 2.0
        else:
            complexity = _non_python_complexity_proxy(metric, churn_norm, bug_density)

        age_risk = _age_risk(metric.get("last_modified"))
        test_touch_ratio = max(0.0, min(float(metric.get("test_touch_ratio", 0.0)), 1.0))
        test_coverage_trend = float(metric.get("test_coverage_trend", 0.0))
        # Lower test touch ratio and negative trend increase risk.
        test_risk = min((1.0 - test_touch_ratio) * 0.75 + max(-test_coverage_trend, 0.0) * 0.25, 1.0)
        test_risk *= 0.6 + 0.4 * sample_confidence

        deployment_frequency = max(0.0, min(float(metric.get("deployment_frequency_per_commit", 0.0)), 1.0))
        # Frequent production-affecting commits per module can signal operational pressure.
        deploy_risk = min(deployment_frequency * 1.2, 1.0)
        deploy_risk *= 0.6 + 0.4 * sample_confidence
        author_count = max(int(metric.get("authors", 1)), 1)
        author_risk = 1.0 - min(author_count / 3.0, 1.0)

        raw_risk = (
            WEIGHTS["churn"] * churn_norm
            + WEIGHTS["bug_density"] * bug_density
            + WEIGHTS["complexity"] * complexity
            + WEIGHTS["age"] * age_risk
            + WEIGHTS["test"] * test_risk
            + WEIGHTS["deploy"] * deploy_risk
            + WEIGHTS["author"] * author_risk
        )
        score = max(0.0, min(100.0, round((1.0 - raw_risk) * 100.0, 1)))
        tier = "green" if score >= 70 else ("yellow" if score >= 40 else "red")

        scored.append(
            {
                **metric,
                "score": score,
                "tier": tier,
                "complexity": round(complexity, 3),
                "bug_density": round(bug_density, 3),
                "churn_rate": round(churn_norm, 3),
                "sample_confidence": round(sample_confidence, 3),
                "test_touch_ratio": round(test_touch_ratio, 3),
                "test_coverage_trend": round(test_coverage_trend, 3),
                "deployment_frequency_per_commit": round(deployment_frequency, 3),
                "test_risk": round(test_risk, 3),
                "deploy_risk": round(deploy_risk, 3),
                "author_risk": round(author_risk, 3),
                "cc": round(float(radon.get("cc", 0.0)), 2),
                "mi": round(float(radon.get("mi", 100.0)), 2),
            }
        )

    return sorted(scored, key=lambda row: row["score"])
