from __future__ import annotations

import uuid
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import settings
from database import Repo, Session

router = APIRouter(tags=["repos"])

GITHUB_API_BASE = "https://api.github.com"
GITLAB_API_BASE = "https://gitlab.com/api/v4"


class RepoCreate(BaseModel):
    url: str = Field(..., examples=["https://github.com/org/repo.git"])
    token: str | None = Field(default=None)


class RepoDiscover(BaseModel):
    provider: str = Field(default="github", pattern="^(github|gitlab)$")
    profile_url: str | None = Field(default=None)
    token: str | None = Field(default=None)


def _normalize_repo_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Repository URL must be HTTP(S)")

    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.strip("/").split("/") if part]

    if host.endswith("github.com") or host.endswith("gitlab.com"):
        if len(path_parts) < 2:
            raise HTTPException(
                status_code=400,
                detail="Provide a full repository URL (owner/repo), not just a user profile URL.",
            )
        owner = path_parts[0]
        repo = path_parts[1].replace(".git", "")
        return f"https://{host}/{owner}/{repo}.git", repo

    if len(path_parts) < 2:
        raise HTTPException(status_code=400, detail="Repository URL path is incomplete")

    repo_name = path_parts[-1].replace(".git", "")
    return url.strip(), repo_name


def _parse_profile_owner(profile_url: str | None, provider: str) -> str | None:
    if not profile_url:
        return None

    cleaned = profile_url.strip()
    parsed = urlparse(cleaned)

    if parsed.scheme in {"http", "https"}:
        host = parsed.netloc.lower()
        path_parts = [part for part in parsed.path.strip("/").split("/") if part]
        if not path_parts:
            raise HTTPException(status_code=400, detail="Profile URL path is incomplete")

        if provider == "github" and not host.endswith("github.com"):
            raise HTTPException(status_code=400, detail="Expected a GitHub profile URL")
        if provider == "gitlab" and not host.endswith("gitlab.com"):
            raise HTTPException(status_code=400, detail="Expected a GitLab profile URL")
        return path_parts[0]

    if "://" in cleaned:
        raise HTTPException(status_code=400, detail="Profile URL must be HTTP(S) or a plain owner name")

    parts = [part for part in cleaned.strip("/").split("/") if part]
    if not parts:
        return None
    return parts[0]


def _request_json(
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
    params: dict[str, str | int] | None = None,
) -> list[dict] | dict:
    response = client.get(url, headers=headers, params=params)
    if response.status_code >= 400:
        detail = response.text.strip().replace("\n", " ")
        if len(detail) > 220:
            detail = f"{detail[:220]}..."
        raise HTTPException(
            status_code=400,
            detail=f"Repository discovery failed ({response.status_code}): {detail or response.reason_phrase}",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Repository discovery returned non-JSON data") from exc

    if isinstance(payload, (dict, list)):
        return payload
    return {}


def _fetch_pages(
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
    params: dict[str, str | int],
) -> list[dict]:
    items: list[dict] = []
    page = 1
    while page <= 5:
        payload = _request_json(client, url, headers=headers, params={**params, "page": page, "per_page": 100})
        if not isinstance(payload, list):
            break
        items.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < 100:
            break
        page += 1
    return items


def _discover_github_repos(profile_url: str | None, token: str | None) -> list[dict]:
    owner = _parse_profile_owner(profile_url, "github")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        if owner:
            repos = _fetch_pages(
                client,
                f"{GITHUB_API_BASE}/users/{owner}/repos",
                headers=headers,
                params={"sort": "updated", "direction": "desc", "type": "all"},
            )
            if not repos and token:
                repos = _fetch_pages(
                    client,
                    f"{GITHUB_API_BASE}/orgs/{owner}/repos",
                    headers=headers,
                    params={"sort": "updated", "direction": "desc", "type": "all"},
                )
        else:
            if not token:
                raise HTTPException(
                    status_code=400,
                    detail="Provide a profile URL/owner name or add a token to discover your repositories.",
                )
            repos = _fetch_pages(
                client,
                f"{GITHUB_API_BASE}/user/repos",
                headers=headers,
                params={
                    "sort": "updated",
                    "direction": "desc",
                    "affiliation": "owner,collaborator,organization_member",
                    "visibility": "all",
                },
            )

    normalized: list[dict] = []
    seen: set[str] = set()
    for repo in repos:
        full_name = str(repo.get("full_name") or "").strip()
        clone_url = str(repo.get("clone_url") or "").strip()
        if not full_name or not clone_url or full_name in seen:
            continue
        seen.add(full_name)
        normalized.append(
            {
                "name": str(repo.get("name") or full_name.split("/")[-1]),
                "full_name": full_name,
                "url": clone_url,
                "private": bool(repo.get("private", False)),
            }
        )
    return sorted(normalized, key=lambda item: item["full_name"].lower())


def _resolve_gitlab_user_id(client: httpx.Client, owner: str, headers: dict[str, str]) -> int | None:
    payload = _request_json(client, f"{GITLAB_API_BASE}/users", headers=headers, params={"username": owner})
    if not isinstance(payload, list):
        return None

    exact = next(
        (row for row in payload if str(row.get("username") or "").lower() == owner.lower()),
        None,
    )
    candidate = exact or (payload[0] if payload else None)
    if not isinstance(candidate, dict):
        return None

    user_id = candidate.get("id")
    if isinstance(user_id, int):
        return user_id
    return None


def _discover_gitlab_repos(profile_url: str | None, token: str | None) -> list[dict]:
    owner = _parse_profile_owner(profile_url, "gitlab")
    headers: dict[str, str] = {}
    if token:
        headers["PRIVATE-TOKEN"] = token

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        if owner:
            user_id = _resolve_gitlab_user_id(client, owner, headers)
            if user_id is None:
                raise HTTPException(status_code=404, detail="GitLab profile not found")
            repos = _fetch_pages(
                client,
                f"{GITLAB_API_BASE}/users/{user_id}/projects",
                headers=headers,
                params={"order_by": "last_activity_at", "sort": "desc", "simple": "true"},
            )
        else:
            if not token:
                raise HTTPException(
                    status_code=400,
                    detail="Provide a profile URL/owner name or add a token to discover your repositories.",
                )
            repos = _fetch_pages(
                client,
                f"{GITLAB_API_BASE}/projects",
                headers=headers,
                params={"membership": "true", "order_by": "last_activity_at", "sort": "desc", "simple": "true"},
            )

    normalized: list[dict] = []
    seen: set[str] = set()
    for repo in repos:
        full_name = str(repo.get("path_with_namespace") or repo.get("name") or "").strip()
        clone_url = str(repo.get("http_url_to_repo") or "").strip()
        if not full_name or not clone_url or full_name in seen:
            continue
        seen.add(full_name)
        visibility = str(repo.get("visibility") or "private").lower()
        normalized.append(
            {
                "name": str(repo.get("name") or full_name.split("/")[-1]),
                "full_name": full_name,
                "url": clone_url,
                "private": visibility != "public",
            }
        )
    return sorted(normalized, key=lambda item: item["full_name"].lower())


@router.post("/repos")
def add_repo(body: RepoCreate) -> dict:
    normalized_url, name = _normalize_repo_url(body.url)
    with Session() as db:
        repo = Repo(id=str(uuid.uuid4()), url=normalized_url, name=name, token=body.token or settings.github_token)
        db.add(repo)
        db.commit()
    return {"id": repo.id, "name": repo.name, "url": repo.url}


@router.post("/repos/discover")
def discover_repos(body: RepoDiscover) -> dict:
    provider = body.provider.lower()
    if provider == "github":
        repos = _discover_github_repos(body.profile_url, body.token or settings.github_token or None)
    else:
        repos = _discover_gitlab_repos(body.profile_url, body.token)

    return {
        "provider": provider,
        "count": len(repos),
        "repos": repos,
    }


@router.get("/repos/{repo_id}")
def get_repo(repo_id: str) -> dict:
    with Session() as db:
        repo = db.get(Repo, repo_id)
        if repo is None:
            raise HTTPException(status_code=404, detail="Repository not found")
        return {"id": repo.id, "name": repo.name, "url": repo.url, "created": repo.created.isoformat()}
