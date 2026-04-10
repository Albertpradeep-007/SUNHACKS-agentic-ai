from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import re

from pydriller import Repository

from config import settings

BUG_PATTERN = re.compile(
    r"\b(fix|bug|patch|issue|defect|error|crash|hotfix|regression)\b",
    re.IGNORECASE,
)
DEPLOY_PATTERN = re.compile(
    r"\b(deploy|release|rollout|production|prod|ship|rollback|hotfix)\b",
    re.IGNORECASE,
)
TEST_PATH_PATTERN = re.compile(r"(^|/)(test|tests|__tests__)(/|$)|(_test\.|\.spec\.)", re.IGNORECASE)
DAYS_BACK = 90
RECENT_WINDOW_DAYS = 30
FALLBACK_DAYS_BACK = 365
CODE_EXTENSIONS = {
    ".py",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".cs",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".php",
    ".rb",
    ".swift",
    ".m",
    ".mm",
    ".scala",
    ".lua",
    ".sh",
    ".ps1",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".cmake",
}
CODE_FILENAMES = {"Dockerfile", "Makefile", "CMakeLists.txt", "Jenkinsfile"}
SKIP_SEGMENTS = {"docs", "documentation", "vendor", "third_party", "third-party", "node_modules"}
GENERATED_FILE_PATTERN = re.compile(
    r"(_bin\.(h|hpp|c|cc|cpp)$|\.generated\.|\.pb\.(h|cc|cpp)$|\.min\.(js|css)$)",
    re.IGNORECASE,
)


def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return bool(TEST_PATH_PATTERN.search(normalized))


def _is_code_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if any(part.lower() in SKIP_SEGMENTS for part in parts[:-1]):
        return False

    filename = parts[-1] if parts else normalized
    if GENERATED_FILE_PATTERN.search(filename):
        return False
    if filename in CODE_FILENAMES:
        return True

    lower = filename.lower()
    if "." not in lower:
        return False

    ext = lower[lower.rfind(".") :]
    return ext in CODE_EXTENSIONS


def _module_priority(sample: dict) -> float:
    return (
        float(sample.get("churn", 0))
        + float(sample.get("bug_fix_count", 0)) * 120.0
        + float(sample.get("deployment_touch_count", 0)) * 60.0
        + (1.0 - float(sample.get("test_touch_ratio", 0.0))) * 35.0
    )


def _mine_repo_window(repo_path: str, days_back: int | None) -> list[dict]:
    since = datetime.now() - timedelta(days=days_back) if days_back is not None else None
    recent_since = datetime.now() - timedelta(days=RECENT_WINDOW_DAYS)
    stats: dict[str, dict] = defaultdict(
        lambda: {
            "module": "",
            "commit_count": 0,
            "bug_fix_count": 0,
            "churn": 0,
            "authors": set(),
            "last_modified": None,
            "test_touched_commits": 0,
            "recent_test_touched_commits": 0,
            "recent_commit_count": 0,
            "deployment_touch_count": 0,
        }
    )
    commits_scanned = 0
    truncated = False
    max_commits = max(int(settings.max_commits_per_window), 1)
    max_files_per_commit = max(int(settings.max_files_per_commit), 1)
    ignored_non_code_files = 0
    skipped_unreadable_commits = 0
    capped_commit_files = 0

    for commit in Repository(repo_path, since=since, only_no_merge=True).traverse_commits():
        commits_scanned += 1
        if commits_scanned > max_commits:
            truncated = True
            break

        try:
            modified_files = list(commit.modified_files)
        except Exception:
            skipped_unreadable_commits += 1
            continue

        if len(modified_files) > max_files_per_commit:
            modified_files = modified_files[:max_files_per_commit]
            capped_commit_files += 1

        is_bugfix = bool(BUG_PATTERN.search(commit.msg or ""))
        is_deploy_commit = bool(DEPLOY_PATTERN.search(commit.msg or ""))
        modified_paths = [
            (modified.new_path or modified.old_path)
            for modified in modified_files
            if (modified.new_path or modified.old_path) and _is_code_path(modified.new_path or modified.old_path)
        ]
        has_test_changes = any(_is_test_path(path) for path in modified_paths)
        is_recent_commit = commit.author_date.replace(tzinfo=None) >= recent_since

        for modified in modified_files:
            path = modified.new_path or modified.old_path
            if not path:
                continue
            if not _is_code_path(path):
                ignored_non_code_files += 1
                continue

            sample = stats[path]
            sample["module"] = path
            sample["commit_count"] += 1
            sample["bug_fix_count"] += 1 if is_bugfix else 0
            sample["churn"] += (modified.added_lines or 0) + (modified.deleted_lines or 0)
            if has_test_changes:
                sample["test_touched_commits"] += 1
            if is_recent_commit:
                sample["recent_commit_count"] += 1
                if has_test_changes:
                    sample["recent_test_touched_commits"] += 1
            if is_deploy_commit:
                sample["deployment_touch_count"] += 1
            if commit.author and commit.author.email:
                sample["authors"].add(commit.author.email.lower())
            sample["last_modified"] = commit.author_date.isoformat()

    result: list[dict] = []
    for sample in stats.values():
        commit_count = max(sample["commit_count"], 1)
        recent_commit_count = sample["recent_commit_count"]
        overall_test_ratio = sample["test_touched_commits"] / commit_count
        if recent_commit_count > 0:
            recent_test_ratio = sample["recent_test_touched_commits"] / recent_commit_count
        else:
            recent_test_ratio = overall_test_ratio

        sample["test_touch_ratio"] = round(overall_test_ratio, 3)
        sample["test_coverage_trend"] = round(recent_test_ratio - overall_test_ratio, 3)
        sample["deployment_frequency_per_commit"] = round(sample["deployment_touch_count"] / commit_count, 3)
        window_days = days_back if days_back is not None else DAYS_BACK
        sample["deployment_frequency_90d"] = round(sample["deployment_touch_count"] / max(window_days, 1), 4)
        sample["commits_scanned"] = commits_scanned
        sample["commit_scan_truncated"] = truncated
        sample["ignored_non_code_files"] = ignored_non_code_files
        sample["skipped_unreadable_commits"] = skipped_unreadable_commits
        sample["capped_commit_files"] = capped_commit_files
        sample["authors"] = len(sample["authors"])
        result.append(sample)

    limited = sorted(result, key=lambda item: (-_module_priority(item), item["module"]))
    return limited[: max(int(settings.max_mined_modules), 1)]


def mine_repo(repo_path: str, days_back: int = DAYS_BACK) -> list[dict]:
    primary = _mine_repo_window(repo_path, days_back)
    if primary:
        for item in primary:
            item["analysis_window_days"] = days_back
            item["is_fallback_window"] = False
            item["is_full_history_window"] = False
        return primary

    fallback_days = max(FALLBACK_DAYS_BACK, days_back)
    fallback = _mine_repo_window(repo_path, fallback_days)
    for item in fallback:
        item["analysis_window_days"] = fallback_days
        item["is_fallback_window"] = True
        item["is_full_history_window"] = False
    if fallback:
        return fallback

    full_history = _mine_repo_window(repo_path, None)
    for item in full_history:
        item["analysis_window_days"] = None
        item["is_fallback_window"] = True
        item["is_full_history_window"] = True
    return full_history
