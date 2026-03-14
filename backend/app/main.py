from __future__ import annotations

import base64
import binascii
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field

from app.api.health import router as health_router
from app.config import get_settings
from app.github_feedback import create_github_issue
from app.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.store import store
from app.synology_integration import get_nsx_status, get_synology_sync_status, pull_synology_notes, save_uploaded_nsx

app = FastAPI(
    title="AI Note Community",
    description="Community edition backend shell for notes, members, backup, search, and graph.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        if len(token.strip()) > 1
    }


def _find_user_by_email(state: dict[str, Any], email: str) -> dict[str, Any] | None:
    return next((user for user in state["users"] if user["email"].lower() == email.lower()), None)


def _find_user_by_id(state: dict[str, Any], user_id: int) -> dict[str, Any] | None:
    return next((user for user in state["users"] if user["user_id"] == user_id), None)


def _serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "org_id": user["org_id"],
        "org_slug": user["org_slug"],
        "role": user["role"],
    }


def _require_initialized(state: dict[str, Any]) -> None:
    if not state["setup"]["initialized"]:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="setup_required")


def _next_counter(state: dict[str, Any], key: str) -> int:
    value = state["counters"][key]
    state["counters"][key] += 1
    return value


def _tokens_for_user(user: dict[str, Any]) -> dict[str, Any]:
    public_user = _serialize_user(user)
    return {
        **public_user,
        "access_token": create_access_token(public_user),
        "refresh_token": create_refresh_token(public_user),
    }


def _token_from_header(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_token")
    return authorization.split(" ", 1)[1]


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = _token_from_header(authorization)
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token") from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    state = store.load()
    _require_initialized(state)
    user_id = int(str(payload["sub"]))
    user = _find_user_by_id(state, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
    return user


def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if current_user["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")
    return current_user


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = ""
    org_name: str | None = None
    org_slug: str | None = None


class SetupLanguageRequest(BaseModel):
    language: str


class SetupAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    password_confirm: str
    name: str = ""
    org_name: str
    org_slug: str


class SetupAIRequest(BaseModel):
    providers: list[dict[str, str]]
    test: bool = False


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class RoleUpdateRequest(BaseModel):
    role: str


class NoteCreateRequest(BaseModel):
    title: str
    content: str
    notebook: str


class NoteUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None


class FeedbackCreateRequest(BaseModel):
    title: str = Field(min_length=4, max_length=120)
    category: str = Field(default="ux", max_length=32)
    priority: str = Field(default="medium", max_length=16)
    page: str = Field(default="/", max_length=120)
    message: str = Field(min_length=12, max_length=4000)
    email: EmailStr | None = None
    create_github_issue: bool = True
    screenshot_data_urls: list[str] = Field(default_factory=list)
    screenshot_names: list[str] = Field(default_factory=list)


def _validate_org_slug(slug: str) -> str:
    normalized = slug.lower().strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,48}[a-z0-9]", normalized):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_org_slug")
    return normalized


def _ensure_workspace_not_initialized(state: dict[str, Any]) -> None:
    if state["setup"]["initialized"] or state["organization"] is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="workspace_already_initialized")


def _create_workspace(
    state: dict[str, Any],
    *,
    email: str,
    password: str,
    name: str,
    org_name: str,
    org_slug: str,
) -> dict[str, Any]:
    _ensure_workspace_not_initialized(state)
    if _find_user_by_email(state, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_exists")

    normalized_slug = _validate_org_slug(org_slug)
    state["organization"] = {
        "id": 1,
        "name": org_name,
        "slug": normalized_slug,
        "created_at": _iso_now(),
    }

    user_id = _next_counter(state, "user")
    owner = {
        "id": user_id,
        "user_id": user_id,
        "email": email,
        "name": name or email.split("@")[0],
        "password_hash": hash_password(password),
        "role": "owner",
        "org_id": 1,
        "org_slug": normalized_slug,
        "accepted_at": _iso_now(),
        "is_pending": False,
    }
    state["users"].append(owner)

    notebook_id = _next_counter(state, "notebook")
    state["notebooks"].append(
        {
            "id": notebook_id,
            "name": "General",
            "description": "Default notebook",
            "category": None,
            "note_count": 0,
        }
    )

    state["setup"]["initialized"] = True
    return owner


def _feedback_labels(category: str, priority: str) -> list[str]:
    settings = get_settings()
    labels = list(settings.github_feedback_labels)
    labels.extend(
        [
            f"category:{category.lower()}",
            f"priority:{priority.lower()}",
        ]
    )
    return labels


def _feedback_issue_body(feedback: dict[str, Any]) -> str:
    details = [
        "## Community Feedback",
        "",
        feedback["message"],
        "",
        "## Context",
        f"- Submitted by: {feedback['submitted_by_name']} <{feedback['submitted_by_email']}>",
        f"- Workspace role: {feedback['submitted_by_role']}",
        f"- Page: {feedback['page']}",
        f"- Category: {feedback['category']}",
        f"- Priority: {feedback['priority']}",
        f"- Feedback ID: {feedback['feedback_id']}",
    ]
    if feedback.get("contact_email"):
        details.append(f"- Follow-up email: {feedback['contact_email']}")
    screenshots = feedback.get("screenshots", [])
    if screenshots:
        details.append(f"- Screenshot attachments in app: {len(screenshots)}")
        for screenshot in screenshots:
            details.append(f"  - {screenshot['asset_name']}")
    return "\n".join(details)


def _screenshot_suffix(content_type: str) -> str:
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }[content_type]


def _normalize_screenshot_name(name: str | None) -> str | None:
    if not name:
        return None
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
    return normalized[:80] or None


def _decode_feedback_screenshot(data_url: str) -> tuple[str, bytes]:
    matched = re.fullmatch(r"data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)", data_url)
    if matched is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_screenshot")
    content_type = matched.group(1)
    try:
        payload = base64.b64decode(matched.group(2), validate=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_screenshot") from exc
    if len(payload) > 4 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="screenshot_too_large")
    return content_type, payload


def _feedback_asset_url(asset_name: str | None) -> str | None:
    if not asset_name:
        return None
    return f"/api/feedback/assets/{asset_name}"


def _prepare_feedback_screenshots(
    data_urls: list[str],
    names: list[str],
) -> list[dict[str, Any]]:
    if len(data_urls) > 3 or len(names) > 3:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="too_many_screenshots")
    if names and len(data_urls) != len(names):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_screenshot_names")

    prepared: list[dict[str, Any]] = []
    for index, data_url in enumerate(data_urls, start=1):
        content_type, payload = _decode_feedback_screenshot(data_url)
        prepared.append(
            {
                "index": index,
                "content_type": content_type,
                "bytes": payload,
                "original_name": _normalize_screenshot_name(names[index - 1] if index - 1 < len(names) else None),
            }
        )
    return prepared


@app.get("/api/setup/status")
async def setup_status() -> dict[str, Any]:
    state = store.load()
    return {
        "initialized": state["setup"]["initialized"],
        "current_step": 4 if state["setup"]["initialized"] else 1,
        "total_steps": 4,
    }


@app.post("/api/setup/language")
async def setup_language(payload: SetupLanguageRequest) -> dict[str, int]:
    def _mutate(state: dict[str, Any]) -> dict[str, int]:
        if state["setup"]["initialized"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already_initialized")
        state["setup"]["language"] = payload.language
        return {"step": 1}

    return store.mutate(_mutate)


@app.post("/api/setup/admin")
async def setup_admin(payload: SetupAdminRequest) -> dict[str, int]:
    if payload.password != payload.password_confirm:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="password_mismatch")

    def _mutate(state: dict[str, Any]) -> dict[str, int]:
        if state["setup"]["initialized"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already_initialized")
        state["setup"]["pending_admin"] = payload.model_dump()
        return {"step": 2}

    return store.mutate(_mutate)


@app.post("/api/setup/ai")
async def setup_ai(payload: SetupAIRequest) -> dict[str, Any]:
    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        state["setup"]["ai_keys"] = {
            item["provider"]: item["api_key"] for item in payload.providers if item.get("api_key")
        }
        return {"step": 3, "test_results": None}

    return store.mutate(_mutate)


@app.post("/api/setup/complete")
async def setup_complete() -> dict[str, Any]:
    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        pending_admin = state["setup"]["pending_admin"]
        if not pending_admin:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="missing_admin")
        owner = _create_workspace(
            state,
            email=pending_admin["email"],
            password=pending_admin["password"],
            name=pending_admin["name"],
            org_name=pending_admin["org_name"],
            org_slug=pending_admin["org_slug"],
        )
        return _tokens_for_user(owner)

    return store.mutate(_mutate)


@app.post("/api/members/signup")
async def member_signup(payload: SignupRequest) -> dict[str, Any]:
    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        if not state["setup"]["initialized"]:
            if not payload.org_name or not payload.org_slug:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="organization_required",
                )
            owner = _create_workspace(
                state,
                email=payload.email,
                password=payload.password,
                name=payload.name,
                org_name=payload.org_name,
                org_slug=payload.org_slug,
            )
            return _tokens_for_user(owner)

        invited_user = _find_user_by_email(state, payload.email)
        if invited_user is None or not invited_user["is_pending"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invite_required")

        invited_user["name"] = payload.name or payload.email.split("@")[0]
        invited_user["password_hash"] = hash_password(payload.password)
        invited_user["accepted_at"] = _iso_now()
        invited_user["is_pending"] = False
        return _tokens_for_user(invited_user)

    return store.mutate(_mutate)


@app.post("/api/auth/login")
async def auth_login(payload: LoginRequest) -> dict[str, Any]:
    state = store.load()
    _require_initialized(state)
    user = _find_user_by_email(state, payload.email)
    if user is None or user["is_pending"] or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    return _tokens_for_user(user)


@app.post("/api/auth/token/refresh")
async def auth_refresh(payload: RefreshRequest) -> dict[str, str]:
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token") from exc
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")
    state = store.load()
    _require_initialized(state)
    user = _find_user_by_id(state, int(str(decoded["sub"])))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
    return {"access_token": create_access_token(_serialize_user(user)), "token_type": "bearer"}


@app.get("/api/auth/me")
async def auth_me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return _serialize_user(current_user)


@app.get("/api/feedback/config")
async def feedback_config(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    _ = current_user
    settings = get_settings()
    return {
        "github_enabled": bool(settings.GITHUB_FEEDBACK_REPO and settings.GITHUB_FEEDBACK_TOKEN),
        "github_repo": settings.GITHUB_FEEDBACK_REPO or None,
        "default_labels": settings.github_feedback_labels,
    }


@app.get("/api/feedback")
async def list_feedback(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    state = store.load()
    is_admin = current_user["role"] in {"owner", "admin"}
    items = state["feedback"]
    if not is_admin:
        items = [item for item in items if item["submitted_by_user_id"] == current_user["user_id"]]
    return {
        "items": items,
        "total": len(items),
        "view_scope": "workspace" if is_admin else "mine",
    }


@app.get("/api/feedback/assets/{asset_name}")
async def feedback_asset(asset_name: str, current_user: dict[str, Any] = Depends(get_current_user)) -> FileResponse:
    state = store.load()
    is_admin = current_user["role"] in {"owner", "admin"}
    feedback_item = next(
        (
            item
            for item in state["feedback"]
            if any(screenshot["asset_name"] == asset_name for screenshot in item.get("screenshots", []))
        ),
        None,
    )
    if feedback_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="feedback_asset_not_found")
    if not is_admin and feedback_item["submitted_by_user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="feedback_asset_forbidden")

    screenshot = next(
        screenshot for screenshot in feedback_item["screenshots"] if screenshot["asset_name"] == asset_name
    )
    asset_path = get_settings().feedback_assets_dir / asset_name
    if not asset_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="feedback_asset_not_found")
    return FileResponse(asset_path, media_type=screenshot["content_type"], filename=asset_name)


@app.post("/api/feedback")
async def create_feedback(
    payload: FeedbackCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    settings = get_settings()
    should_create_github_issue = bool(
        payload.create_github_issue and settings.GITHUB_FEEDBACK_REPO and settings.GITHUB_FEEDBACK_TOKEN
    )
    prepared_screenshots = _prepare_feedback_screenshots(payload.screenshot_data_urls, payload.screenshot_names)

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        feedback_seq = _next_counter(state, "feedback")
        screenshots: list[dict[str, Any]] = []
        for screenshot in prepared_screenshots:
            asset_name = (
                f"feedback-{feedback_seq:05d}-{screenshot['index']}"
                f"{_screenshot_suffix(screenshot['content_type'])}"
            )
            screenshots.append(
                {
                    "asset_name": asset_name,
                    "asset_url": _feedback_asset_url(asset_name),
                    "content_type": screenshot["content_type"],
                    "original_name": screenshot["original_name"],
                }
            )
        feedback = {
            "id": feedback_seq,
            "feedback_id": f"FDBK-{feedback_seq:05d}",
            "title": payload.title.strip(),
            "category": payload.category.strip().lower(),
            "priority": payload.priority.strip().lower(),
            "page": payload.page.strip() or "/",
            "message": payload.message.strip(),
            "contact_email": str(payload.email) if payload.email else None,
            "submitted_by_user_id": current_user["user_id"],
            "submitted_by_email": current_user["email"],
            "submitted_by_name": current_user["name"],
            "submitted_by_role": current_user["role"],
            "status": "received",
            "created_at": _iso_now(),
            "github_sync_status": "pending" if should_create_github_issue else "not_requested",
            "github_issue_number": None,
            "github_issue_url": None,
            "github_error": None,
            "screenshots": screenshots,
        }
        state["feedback"].insert(0, feedback)
        return feedback

    feedback = store.mutate(_mutate)
    for screenshot, metadata in zip(prepared_screenshots, feedback["screenshots"], strict=False):
        asset_path = settings.feedback_assets_dir / metadata["asset_name"]
        asset_path.write_bytes(screenshot["bytes"])
    if not payload.create_github_issue:
        return feedback
    if not should_create_github_issue:
        def _mark_disabled(state: dict[str, Any]) -> dict[str, Any]:
            item = next(entry for entry in state["feedback"] if entry["feedback_id"] == feedback["feedback_id"])
            item["github_sync_status"] = "disabled"
            return item

        return store.mutate(_mark_disabled)

    github_result = await create_github_issue(
        title=f"[{feedback['category']}] {feedback['title']}",
        body=_feedback_issue_body(feedback),
        labels=_feedback_labels(feedback["category"], feedback["priority"]),
    )

    def _apply_github_result(state: dict[str, Any]) -> dict[str, Any]:
        item = next(entry for entry in state["feedback"] if entry["feedback_id"] == feedback["feedback_id"])
        item["github_sync_status"] = github_result["status"]
        item["github_issue_number"] = github_result.get("issue_number")
        item["github_issue_url"] = github_result.get("issue_url")
        item["github_error"] = github_result.get("error")
        return item

    return store.mutate(_apply_github_result)


@app.get("/api/notebooks")
async def list_notebooks(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    return {"items": state["notebooks"], "total": len(state["notebooks"])}


@app.get("/api/notes")
async def list_notes(
    search: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    notes = state["notes"]
    if search:
        lowered = search.lower()
        notes = [
            note
            for note in notes
            if lowered in note["title"].lower() or lowered in note["content"].lower()
        ]
    total = len(notes)
    items = notes[offset : offset + limit]
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@app.post("/api/notes")
async def create_note(
    payload: NoteCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        note_id = str(_next_counter(state, "note"))
        timestamp = _iso_now()
        note = {
            "note_id": note_id,
            "title": payload.title,
            "content": payload.content,
            "notebook": payload.notebook,
            "created_at": timestamp,
            "updated_at": timestamp,
            "tags": [],
            "source": None,
            "source_note_id": None,
            "source_notebook_id": None,
            "source_updated_at": None,
            "synced_at": None,
            "sync_status": None,
            "remote_conflict_data": None,
        }
        state["notes"].insert(0, note)
        for notebook in state["notebooks"]:
            if notebook["name"] == payload.notebook:
                notebook["note_count"] += 1
                break
        return note

    return store.mutate(_mutate)


@app.get("/api/notes/{note_id}")
async def get_note(note_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    note = next((item for item in state["notes"] if item["note_id"] == note_id), None)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note_not_found")
    return note


@app.put("/api/notes/{note_id}")
async def update_note(
    note_id: str,
    payload: NoteUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        note = next((item for item in state["notes"] if item["note_id"] == note_id), None)
        if note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note_not_found")
        if payload.title is not None:
            note["title"] = payload.title
        if payload.content is not None:
            note["content"] = payload.content
        note["updated_at"] = _iso_now()
        if note.get("source") == "synology":
            note["sync_status"] = "local_modified"
        return note

    return store.mutate(_mutate)


@app.get("/api/search")
async def search_notes(
    q: str = Query(min_length=1),
    type: str = Query(default="search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    _ = (type, current_user)
    state = store.load()
    query_tokens = _tokenize(q)

    results: list[dict[str, Any]] = []
    for note in state["notes"]:
        haystack = f"{note['title']} {note['content']}".lower()
        haystack_tokens = _tokenize(haystack)
        overlap = len(query_tokens & haystack_tokens)
        if overlap == 0 and q.lower() not in haystack:
            continue
        denom = max(len(query_tokens | haystack_tokens), 1)
        score = overlap / denom if overlap else 0.15
        results.append(
            {
                "note_id": note["note_id"],
                "title": note["title"],
                "snippet": note["content"][:180],
                "score": score,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    paginated = results[offset : offset + limit]
    return {
        "results": paginated,
        "query": q,
        "search_type": "search",
        "total": len(results),
    }


@app.get("/api/search/index/status")
async def search_index_status(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    total_notes = len(state["notes"])
    return {
        "status": "completed" if state["setup"]["initialized"] else "idle",
        "total_notes": total_notes,
        "indexed_notes": total_notes,
        "pending_notes": 0,
        "stale_notes": 0,
    }


@app.post("/api/search/index")
async def trigger_search_index(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    return {"message": "index_complete", "pending_notes": 0, "indexed_notes": len(state["notes"])}


@app.get("/api/graph")
async def graph_data(
    limit: int = Query(default=200, ge=1),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    notes = state["notes"][:limit]
    nodes = [
        {
            "id": int(note["note_id"]),
            "label": note["title"] or f"Note {note['note_id']}",
            "notebook": note["notebook"],
            "size": 8,
        }
        for note in notes
    ]

    token_sets = {
        note["note_id"]: _tokenize(f"{note['title']} {note['content']}")
        for note in notes
    }
    links: list[dict[str, Any]] = []
    for index, left in enumerate(notes):
        left_tokens = token_sets[left["note_id"]]
        if not left_tokens:
            continue
        for right in notes[index + 1 :]:
            right_tokens = token_sets[right["note_id"]]
            if not right_tokens:
                continue
            union = left_tokens | right_tokens
            if not union:
                continue
            weight = len(left_tokens & right_tokens) / len(union)
            if weight >= 0.08:
                links.append(
                    {
                        "source": int(left["note_id"]),
                        "target": int(right["note_id"]),
                        "weight": round(weight, 4),
                    }
                )
    return {
        "nodes": nodes,
        "links": links,
        "total_notes": len(state["notes"]),
        "indexed_notes": len(state["notes"]),
    }


@app.get("/api/members")
async def list_members(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    members = [
        {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "accepted_at": user["accepted_at"],
            "is_pending": user["is_pending"],
        }
        for user in state["users"]
    ]
    return {"members": members, "total": len(members)}


@app.post("/api/members/invite")
async def invite_member(
    payload: InviteRequest,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    _ = current_user

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        if _find_user_by_email(state, payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_exists")
        user_id = _next_counter(state, "user")
        invited_user = {
            "id": user_id,
            "user_id": user_id,
            "email": payload.email,
            "name": "",
            "password_hash": hash_password("temporary-password"),
            "role": payload.role,
            "org_id": state["organization"]["id"],
            "org_slug": state["organization"]["slug"],
            "accepted_at": None,
            "is_pending": True,
        }
        state["users"].append(invited_user)
        return {
            "invite_token": f"invite-{user_id}",
            "email": payload.email,
            "role": payload.role,
            "expires_at": _iso_now(),
        }

    return store.mutate(_mutate)


@app.put("/api/members/{member_id}/role")
async def update_member_role(
    member_id: int,
    payload: RoleUpdateRequest,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    _ = current_user

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        user = _find_user_by_id(state, member_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member_not_found")
        if user["role"] == "owner":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_change_owner")
        user["role"] = payload.role
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "accepted_at": user["accepted_at"],
            "is_pending": user["is_pending"],
        }

    return store.mutate(_mutate)


@app.delete("/api/members/{member_id}")
async def remove_member(
    member_id: int,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    _ = current_user

    def _mutate(state: dict[str, Any]) -> dict[str, str]:
        user = _find_user_by_id(state, member_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member_not_found")
        if user["role"] == "owner":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_remove_owner")
        state["users"] = [item for item in state["users"] if item["user_id"] != member_id]
        return {"message": "removed"}

    return store.mutate(_mutate)


@app.get("/api/snapshots")
async def list_snapshots(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    snapshots = state["snapshots"][skip : skip + limit]
    return {"snapshots": snapshots, "total": len(state["snapshots"])}


@app.post("/api/snapshots/full")
async def snapshot_full(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    snapshot = store.snapshot_state("full")
    return {"message": "snapshot_created", "snapshot_id": snapshot["snapshot_id"]}


@app.post("/api/snapshots/incremental")
async def snapshot_incremental(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    snapshot = store.snapshot_state("incremental")
    return {"message": "snapshot_created", "snapshot_id": snapshot["snapshot_id"]}


@app.post("/api/snapshots/{snapshot_id}/restore")
async def snapshot_restore(
    snapshot_id: str,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    _ = current_user
    try:
        return store.restore_snapshot(snapshot_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="snapshot_not_found") from exc


@app.get("/api/snapshots/scheduler/status")
async def snapshot_scheduler_status(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    state = store.load()
    last_snapshot = state["snapshots"][0]["created_at"] if state["snapshots"] else None
    return {
        "running": False,
        "backup_enabled": False,
        "next_full_at": None,
        "next_incremental_at": None,
        "last_snapshot_at": last_snapshot,
    }


@app.get("/api/nsx/status")
async def nsx_import_status(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    return get_nsx_status()


@app.post("/api/nsx/import")
async def nsx_import(
    archive: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    _ = current_user
    filename = archive.filename or "import.nsx"
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=Path(filename).suffix or ".nsx") as temp_file:
            while chunk := await archive.read(1024 * 1024):
                temp_file.write(chunk)
            temp_path = Path(temp_file.name)
        return save_uploaded_nsx(temp_path, filename)
    finally:
        await archive.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@app.get("/api/synology/status")
async def synology_status(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    return get_synology_sync_status()


@app.post("/api/synology/pull")
async def synology_pull(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    _ = current_user
    return await pull_synology_notes()
