from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.config import get_settings
from app.services.nsx_parser import NsxParser
from app.store import store
from app.synology_gateway.client import (
    Synology2FARequiredError,
    SynologyApiError,
    SynologyAuthError,
    SynologyClient,
)
from app.synology_gateway.notestation import NoteStationService


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _coerce_datetime(value: int | float | str | None) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return value
    timestamp = float(value)
    if timestamp > 10_000_000_000:
        timestamp /= 1000
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def _coerce_tags(raw: Any) -> list[str]:
    if isinstance(raw, list):
        tags: list[str] = []
        for item in raw:
            value = item.get("name") or item.get("title") or item.get("value") if isinstance(item, dict) else item
            if value:
                tags.append(str(value))
        return tags
    if isinstance(raw, dict):
        tags = []
        for value in raw.values():
            if isinstance(value, dict):
                tag_name = value.get("name") or value.get("title") or value.get("value")
            else:
                tag_name = value
            if tag_name:
                tags.append(str(tag_name))
        return tags
    return []


def _ensure_notebook(state: dict[str, Any], notebook_name: str | None) -> str:
    target = (notebook_name or "Imported").strip() or "Imported"
    existing = next((item for item in state["notebooks"] if item["name"] == target), None)
    if existing is not None:
        return existing["name"]

    notebook_id = state["counters"]["notebook"]
    state["counters"]["notebook"] += 1
    state["notebooks"].append(
        {
            "id": notebook_id,
            "name": target,
            "description": "Imported from Synology Note Station",
            "category": None,
            "note_count": 0,
        }
    )
    return target


def _increment_notebook_count(state: dict[str, Any], notebook_name: str | None, delta: int) -> None:
    if not notebook_name:
        return
    notebook = next((item for item in state["notebooks"] if item["name"] == notebook_name), None)
    if notebook is None:
        return
    notebook["note_count"] = max(0, int(notebook.get("note_count", 0)) + delta)


def _status_block(state: dict[str, Any], key: str) -> dict[str, Any]:
    return state["integrations"][key]


def get_nsx_status() -> dict[str, Any]:
    state = store.load()
    return dict(_status_block(state, "nsx_import"))


def get_synology_sync_status() -> dict[str, Any]:
    state = store.load()
    status_block = dict(_status_block(state, "synology_sync"))
    settings = get_settings()
    status_block["configured"] = bool(settings.SYNOLOGY_URL and settings.SYNOLOGY_USER and settings.SYNOLOGY_PASSWORD)
    return status_block


def _upsert_imported_note(
    state: dict[str, Any],
    *,
    source: str,
    source_note_id: str,
    title: str,
    content: str,
    notebook_name: str | None,
    tags: list[str],
    source_notebook_id: str | None,
    source_updated_at: str | None,
) -> str:
    existing = next(
        (
            note
            for note in state["notes"]
            if note.get("source") == source and note.get("source_note_id") == source_note_id
        ),
        None,
    )
    target_notebook = _ensure_notebook(state, notebook_name)
    if existing is None:
        note_id = str(state["counters"]["note"])
        state["counters"]["note"] += 1
        timestamp = _iso_now()
        state["notes"].insert(
            0,
            {
                "note_id": note_id,
                "title": title,
                "content": content,
                "notebook": target_notebook,
                "created_at": source_updated_at or timestamp,
                "updated_at": source_updated_at or timestamp,
                "tags": tags,
                "source": source,
                "source_note_id": source_note_id,
                "source_notebook_id": source_notebook_id,
                "source_updated_at": source_updated_at,
                "synced_at": timestamp,
                "sync_status": "synced",
                "remote_conflict_data": None,
            },
        )
        _increment_notebook_count(state, target_notebook, 1)
        return "added"

    original_notebook = existing.get("notebook")
    existing["title"] = title
    existing["content"] = content
    existing["notebook"] = target_notebook
    existing["tags"] = tags
    existing["updated_at"] = source_updated_at or _iso_now()
    existing["source_notebook_id"] = source_notebook_id
    existing["source_updated_at"] = source_updated_at
    existing["synced_at"] = _iso_now()
    existing["sync_status"] = "synced"
    existing["remote_conflict_data"] = None
    if original_notebook != target_notebook:
        _increment_notebook_count(state, original_notebook, -1)
        _increment_notebook_count(state, target_notebook, 1)
    return "updated"


def import_nsx_archive(nsx_path: Path, filename: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    parser = NsxParser(nsx_path=nsx_path, output_dir=settings.nsx_images_dir)
    parsed = parser.parse()

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        added = 0
        updated = 0
        for record in parsed.notes:
            outcome = _upsert_imported_note(
                state,
                source="nsx",
                source_note_id=record.note_id,
                title=record.title or f"Imported note {record.note_id}",
                content=record.content_html or "",
                notebook_name=record.notebook_name,
                tags=_coerce_tags(record.tags),
                source_notebook_id=record.parent_id,
                source_updated_at=_coerce_datetime(record.mtime or record.ctime),
            )
            if outcome == "added":
                added += 1
            else:
                updated += 1

        status_block = _status_block(state, "nsx_import")
        status_block.update(
            {
                "status": "completed" if not parsed.errors else "completed_with_errors",
                "filename": filename or nsx_path.name,
                "notes_processed": parsed.notes_processed,
                "notes_added": added,
                "notes_updated": updated,
                "images_extracted": parsed.images_extracted,
                "errors": parsed.errors,
                "last_import_at": _iso_now(),
            }
        )
        return dict(status_block)

    return store.mutate(_mutate)


def _merge_note_payload(
    summary: dict[str, Any],
    detail: dict[str, Any],
    notebook_map: dict[str, str],
) -> dict[str, Any]:
    parent_id = detail.get("parent_id") or summary.get("parent_id")
    parent_id_str = str(parent_id) if parent_id is not None else None
    return {
        "source_note_id": str(detail.get("object_id") or summary.get("object_id") or ""),
        "title": str(detail.get("title") or summary.get("title") or ""),
        "content": str(detail.get("content") or summary.get("content") or ""),
        "tags": detail.get("tag") or summary.get("tag"),
        "notebook_name": notebook_map.get(parent_id_str) if parent_id_str else None,
        "source_notebook_id": parent_id_str,
        "source_updated_at": _coerce_datetime(detail.get("mtime") or summary.get("mtime")),
    }


async def pull_synology_notes() -> dict[str, Any]:
    settings = get_settings()
    if not (settings.SYNOLOGY_URL and settings.SYNOLOGY_USER and settings.SYNOLOGY_PASSWORD):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="synology_not_configured")

    try:
        async with SynologyClient(settings.SYNOLOGY_URL, settings.SYNOLOGY_USER, settings.SYNOLOGY_PASSWORD) as client:
            service = NoteStationService(client)
            notebook_map = {
                str(item.get("object_id") or item.get("notebook_id")): str(item.get("name") or item.get("title") or "")
                for item in await service.list_notebooks()
                if item.get("object_id") or item.get("notebook_id")
            }
            notes_payload = await service.list_notes()
            remote_notes = notes_payload.get("notes", [])

            detailed_notes: list[dict[str, Any]] = []
            for summary in remote_notes:
                source_note_id = str(summary.get("object_id") or "")
                detail = await service.get_note(source_note_id)
                detailed_notes.append(_merge_note_payload(summary, detail, notebook_map))
    except Synology2FARequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="synology_2fa_required") from exc
    except SynologyAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="synology_auth_failed") from exc
    except SynologyApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"synology_api_error:{exc.code}") from exc

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        current_remote_ids = {item["source_note_id"] for item in detailed_notes}

        added = 0
        updated = 0
        skipped = 0
        conflicts = 0

        for payload in detailed_notes:
            existing = next(
                (
                    note
                    for note in state["notes"]
                    if note.get("source") == "synology" and note.get("source_note_id") == payload["source_note_id"]
                ),
                None,
            )
            if existing is not None and existing.get("sync_status") == "local_modified":
                remote_updated = payload["source_updated_at"]
                local_remote_updated = existing.get("source_updated_at")
                if remote_updated and remote_updated != local_remote_updated:
                    existing["sync_status"] = "conflict"
                    existing["remote_conflict_data"] = {
                        "title": payload["title"],
                        "content": payload["content"],
                        "source_updated_at": remote_updated,
                    }
                    existing["synced_at"] = _iso_now()
                    conflicts += 1
                    continue
                skipped += 1
                continue

            outcome = _upsert_imported_note(
                state,
                source="synology",
                source_note_id=payload["source_note_id"],
                title=payload["title"] or f"Synology note {payload['source_note_id']}",
                content=payload["content"],
                notebook_name=payload["notebook_name"],
                tags=_coerce_tags(payload["tags"]),
                source_notebook_id=payload["source_notebook_id"],
                source_updated_at=payload["source_updated_at"],
            )
            if outcome == "added":
                added += 1
            else:
                updated += 1

        remote_missing = 0
        for note in state["notes"]:
            if note.get("source") != "synology":
                continue
            if note.get("source_note_id") not in current_remote_ids and note.get("sync_status") != "remote_missing":
                note["sync_status"] = "remote_missing"
                note["synced_at"] = _iso_now()
                remote_missing += 1

        status_block = _status_block(state, "synology_sync")
        status_block.update(
            {
                "status": "completed",
                "configured": True,
                "last_synced_at": _iso_now(),
                "added": added,
                "updated": updated,
                "skipped": skipped,
                "remote_missing": remote_missing,
                "conflicts": conflicts,
                "error": None,
            }
        )
        return dict(status_block)

    return store.mutate(_mutate)


def save_uploaded_nsx(temp_path: Path, filename: str | None) -> dict[str, Any]:
    settings = get_settings()
    destination = settings.nsx_imports_dir / (filename or temp_path.name)
    shutil.copyfile(temp_path, destination)
    return import_nsx_archive(destination, filename=filename)
