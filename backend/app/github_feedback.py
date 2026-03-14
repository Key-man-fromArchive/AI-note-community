from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


async def create_github_issue(*, title: str, body: str, labels: list[str]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.GITHUB_FEEDBACK_REPO or not settings.GITHUB_FEEDBACK_TOKEN:
        return {"status": "disabled", "issue_number": None, "issue_url": None, "error": None}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"https://api.github.com/repos/{settings.GITHUB_FEEDBACK_REPO}/issues",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {settings.GITHUB_FEEDBACK_TOKEN}",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={
                    "title": title,
                    "body": body,
                    "labels": labels,
                },
            )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return {
            "status": "failed",
            "issue_number": None,
            "issue_url": None,
            "error": str(exc),
        }

    payload = response.json()
    return {
        "status": "created",
        "issue_number": payload.get("number"),
        "issue_url": payload.get("html_url"),
        "error": None,
    }
