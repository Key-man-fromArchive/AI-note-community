from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from app.config import get_settings

_LOCK = Lock()


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _default_state() -> dict[str, Any]:
    return {
        "setup": {
            "initialized": False,
            "language": "en",
            "pending_admin": None,
            "ai_keys": {},
        },
        "organization": None,
        "users": [],
        "notebooks": [],
        "notes": [],
        "feedback": [],
        "snapshots": [],
        "counters": {
            "user": 1,
            "notebook": 1,
            "note": 1,
            "feedback": 1,
            "snapshot": 1,
        },
        "updated_at": _iso_now(),
    }


class JsonStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.settings.feedback_assets_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        with _LOCK:
            if not self.settings.state_file.exists():
                state = _default_state()
                self._write_state(state)
                return state
            return json.loads(self.settings.state_file.read_text(encoding="utf-8"))

    def save(self, state: dict[str, Any]) -> dict[str, Any]:
        with _LOCK:
            state["updated_at"] = _iso_now()
            self._write_state(state)
            return state

    def mutate(self, callback):
        with _LOCK:
            if not self.settings.state_file.exists():
                state = _default_state()
            else:
                state = json.loads(self.settings.state_file.read_text(encoding="utf-8"))
            result = callback(state)
            state["updated_at"] = _iso_now()
            self._write_state(state)
            return result

    def snapshot_state(self, snapshot_type: str) -> dict[str, Any]:
        def _mutate(state: dict[str, Any]) -> dict[str, Any]:
            snapshot_seq = state["counters"]["snapshot"]
            state["counters"]["snapshot"] += 1
            snapshot_id = f"{snapshot_type}-{snapshot_seq:05d}"
            snapshot = {
                "id": snapshot_seq,
                "snapshot_id": snapshot_id,
                "snapshot_type": snapshot_type,
                "status": "completed",
                "encrypted": False,
                "total_size_bytes": 0,
                "created_at": _iso_now(),
                "completed_at": _iso_now(),
                "error_message": None,
            }
            snapshot_payload = deepcopy(state)
            snapshot_payload["snapshots"] = []
            snapshot_file = self.settings.snapshots_dir / f"{snapshot_id}.json"
            snapshot_file.write_text(
                json.dumps(snapshot_payload, ensure_ascii=True, indent=2),
                encoding="utf-8",
            )
            snapshot["total_size_bytes"] = snapshot_file.stat().st_size
            state["snapshots"].insert(0, snapshot)
            return snapshot

        return self.mutate(_mutate)

    def restore_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        snapshot_file = self.settings.snapshots_dir / f"{snapshot_id}.json"
        if not snapshot_file.exists():
            raise FileNotFoundError(snapshot_id)

        restored_state = json.loads(snapshot_file.read_text(encoding="utf-8"))

        with _LOCK:
            if not self.settings.state_file.exists():
                current_state = _default_state()
            else:
                current_state = json.loads(self.settings.state_file.read_text(encoding="utf-8"))
            restored_state["snapshots"] = current_state.get("snapshots", [])
            counters = restored_state.setdefault("counters", {})
            current_snapshot_counter = current_state.get("counters", {}).get("snapshot", 1)
            counters["snapshot"] = max(counters.get("snapshot", 1), current_snapshot_counter)
            restored_state["updated_at"] = _iso_now()
            self._write_state(restored_state)

        matching = next(
            (snapshot for snapshot in restored_state["snapshots"] if snapshot["snapshot_id"] == snapshot_id),
            None,
        )
        if matching is None:
            raise FileNotFoundError(snapshot_id)
        return matching

    def _write_state(self, state: dict[str, Any]) -> None:
        self.settings.state_file.write_text(
            json.dumps(state, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )


store = JsonStore()
