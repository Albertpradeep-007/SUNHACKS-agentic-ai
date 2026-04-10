from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _run_radon(command: list[str], timeout_seconds: int = 120) -> dict:
    proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Radon command failed")
    stdout = proc.stdout.strip()
    if not stdout:
        return {}
    return json.loads(stdout)


def _average_complexity(cc_blocks: object) -> float:
    if not isinstance(cc_blocks, list):
        return 0.0
    values = []
    for block in cc_blocks:
        if isinstance(block, dict):
            values.append(float(block.get("complexity", 0.0)))
    if not values:
        return 0.0
    return sum(values) / len(values)


def _read_mi(mi_entry: object) -> float:
    if isinstance(mi_entry, (float, int)):
        return float(mi_entry)
    if isinstance(mi_entry, dict):
        if isinstance(mi_entry.get("mi"), (float, int)):
            return float(mi_entry["mi"])
        if isinstance(mi_entry.get("value"), (float, int)):
            return float(mi_entry["value"])
        if isinstance(mi_entry.get("score"), (float, int)):
            return float(mi_entry["score"])
    return 100.0


def _relpath(path: str, repo_path: str) -> str:
    path_obj = Path(path)
    if not path_obj.is_absolute():
        return path.replace("\\", "/")
    try:
        return os.path.relpath(path, repo_path).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def _python_targets(repo_path: str, target_paths: list[str] | None) -> list[str]:
    if not target_paths:
        return [repo_path]

    files: list[str] = []
    for rel in target_paths:
        path = Path(repo_path) / rel
        if path.is_file() and path.suffix.lower() == ".py":
            files.append(str(path))
    return files


def get_radon_scores(repo_path: str, target_paths: list[str] | None = None) -> dict[str, dict[str, float]]:
    """Return {filepath: {"cc": float, "mi": float}} parsed from radon cc/mi JSON."""
    result: dict[str, dict[str, float]] = {}
    targets = _python_targets(repo_path, target_paths)
    if not targets:
        return result

    try:
        cc_data = _run_radon(["radon", "cc", *targets, "-j"])
        mi_data = _run_radon(["radon", "mi", *targets, "-j"])
        all_paths = set(cc_data.keys()) | set(mi_data.keys())

        for path in all_paths:
            avg_cc = _average_complexity(cc_data.get(path, []))
            mi = _read_mi(mi_data.get(path, {}))
            result[_relpath(path, repo_path)] = {"cc": round(avg_cc, 3), "mi": round(mi, 3)}
    except Exception as exc:
        print(f"Radon error: {exc}")
    return result
