from __future__ import annotations

from pathlib import Path
import shutil
from urllib.parse import urlparse

import git


def _repo_dir_name(repo_url: str) -> str:
    parsed = urlparse(repo_url)
    repo_path = parsed.path.strip("/").replace(".git", "")
    # Normalize case to avoid duplicate clones for mixed-case owner names.
    return (repo_path.replace("/", "__") or "repo").lower()


def _auth_url(repo_url: str, token: str | None) -> str:
    if not token:
        return repo_url
    if repo_url.startswith("https://"):
        return repo_url.replace("https://", f"https://{token}@", 1)
    return repo_url


def _is_valid_repo(path: Path) -> bool:
    git_dir = path / ".git"
    if not git_dir.exists():
        return False
    try:
        repo = git.Repo(str(path))
        _ = repo.head.commit.hexsha
        return True
    except Exception:
        return False


def _clone_repo(repo_url: str, token: str | None, target: Path, depth: int, no_checkout: bool) -> None:
    auth_url = _auth_url(repo_url, token)
    kwargs = {
        "single_branch": True,
        "depth": depth,
        "no_checkout": no_checkout,
        "multi_options": ["--no-tags"],
    }
    if depth <= 0:
        kwargs = {"single_branch": True, "no_checkout": no_checkout, "multi_options": ["--no-tags"]}

    try:
        git.Repo.clone_from(auth_url, str(target), **kwargs)
    except Exception:
        # Fall back to full clone when shallow options are unsupported by a host.
        git.Repo.clone_from(auth_url, str(target))


def clone_or_pull(
    repo_url: str,
    token: str | None,
    dest_dir: str,
    clone_depth: int = 0,
    timeout_seconds: int = 1800,
    no_checkout: bool = False,
) -> str:
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    repo_name = _repo_dir_name(repo_url)
    repo_path = Path(dest_dir) / repo_name

    if repo_path.exists() and not _is_valid_repo(repo_path):
        # Remove broken/incomplete clone directories before retrying.
        shutil.rmtree(repo_path, ignore_errors=True)

    if repo_path.exists() and _is_valid_repo(repo_path):
        repo = git.Repo(str(repo_path))
        try:
            repo.remotes.origin.pull()
        except Exception:
            repo.remotes.origin.fetch(prune=True)
    else:
        _clone_repo(repo_url, token, repo_path, clone_depth, no_checkout)

    return str(repo_path)
