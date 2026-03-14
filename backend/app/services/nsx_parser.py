from __future__ import annotations

import json
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AttachmentInfo:
    note_id: str
    ref: str
    name: str
    md5: str
    file_path: Path
    width: int | None = None
    height: int | None = None
    mime_type: str = "application/octet-stream"


@dataclass
class NoteRecord:
    note_id: str
    title: str
    content_html: str
    tags: list | dict | None
    parent_id: str | None
    notebook_name: str | None
    category: str | None
    ctime: int | float | None
    mtime: int | float | None


@dataclass
class NsxParseResult:
    notes_processed: int = 0
    images_extracted: int = 0
    errors: list[str] = field(default_factory=list)
    attachments: list[AttachmentInfo] = field(default_factory=list)
    notes: list[NoteRecord] = field(default_factory=list)


class NsxParser:
    def __init__(self, nsx_path: str | Path, output_dir: str | Path) -> None:
        self.nsx_path = Path(nsx_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse(self) -> NsxParseResult:
        result = NsxParseResult()
        if not self.nsx_path.exists():
            result.errors.append(f"NSX file not found: {self.nsx_path}")
            return result

        try:
            with zipfile.ZipFile(self.nsx_path, "r") as nsx:
                config = self._parse_config(nsx)
                if config is None:
                    result.errors.append("Failed to parse config.json")
                    return result

                note_ids = config.get("note", [])
                notebook_map = self._parse_notebooks(nsx, config)

                for note_id in note_ids:
                    try:
                        note_data = self._read_note_data(nsx, note_id)
                        if note_data is None:
                            result.errors.append(f"Failed to read note {note_id}")
                            continue

                        attachments = self._extract_attachments(nsx, str(note_id), note_data)
                        result.attachments.extend(attachments)
                        result.images_extracted += len(attachments)
                        result.notes_processed += 1

                        note_record = self._build_note_record(str(note_id), note_data, notebook_map)
                        if note_record is not None:
                            result.notes.append(note_record)
                    except Exception as exc:  # pragma: no cover - defensive
                        result.errors.append(f"Error processing note {note_id}: {exc}")
                        logger.warning("Error processing note %s: %s", note_id, exc)
        except zipfile.BadZipFile:
            result.errors.append(f"Invalid ZIP/NSX file: {self.nsx_path}")
        except Exception as exc:  # pragma: no cover - defensive
            result.errors.append(f"Unexpected error: {exc}")
            logger.exception("Unexpected error parsing NSX file")

        return result

    def _parse_config(self, nsx: zipfile.ZipFile) -> dict | None:
        try:
            return json.loads(nsx.read("config.json").decode("utf-8"))
        except (KeyError, json.JSONDecodeError):
            return None

    def _read_note_data(self, nsx: zipfile.ZipFile, note_id: str) -> dict | None:
        try:
            return json.loads(nsx.read(note_id).decode("utf-8"))
        except (KeyError, json.JSONDecodeError):
            return None

    def _extract_attachments(self, nsx: zipfile.ZipFile, note_id: str, note: dict) -> list[AttachmentInfo]:
        attachments: list[AttachmentInfo] = []
        att_dict = note.get("attachment", {})
        if not isinstance(att_dict, dict):
            return attachments

        for ref, meta in att_dict.items():
            if not isinstance(meta, dict):
                continue
            md5 = str(meta.get("md5", "")).strip()
            name = str(meta.get("name", ref))
            if not md5:
                continue

            mime_type = str(meta.get("type", ""))
            if not self._is_image(mime_type, name):
                continue

            try:
                file_data = nsx.read(f"file_{md5}")
            except KeyError:
                logger.warning("Attachment file not found in NSX: %s", md5)
                continue

            note_dir = self.output_dir / note_id
            note_dir.mkdir(parents=True, exist_ok=True)
            file_path = note_dir / self._sanitize_filename(str(ref))
            file_path.write_bytes(file_data)
            attachments.append(
                AttachmentInfo(
                    note_id=note_id,
                    ref=str(ref),
                    name=name,
                    md5=md5,
                    file_path=file_path,
                    width=meta.get("width"),
                    height=meta.get("height"),
                    mime_type=mime_type or self._guess_mime_type(name),
                )
            )
        return attachments

    @staticmethod
    def _build_note_record(note_id: str, note: dict, notebook_map: dict[str, str]) -> NoteRecord | None:
        if not isinstance(note, dict):
            return None
        parent_id = note.get("parent_id")
        parent_id_str = str(parent_id) if parent_id else None
        return NoteRecord(
            note_id=note_id,
            title=str(note.get("title", "")),
            content_html=str(note.get("content", "")),
            tags=note.get("tag"),
            parent_id=parent_id_str,
            notebook_name=notebook_map.get(parent_id_str) if parent_id_str else None,
            category=note.get("category"),
            ctime=note.get("ctime"),
            mtime=note.get("mtime"),
        )

    @staticmethod
    def _parse_notebooks(nsx: zipfile.ZipFile, config: dict) -> dict[str, str]:
        notebook_ids = config.get("notebook", [])
        if not isinstance(notebook_ids, list):
            return {}

        notebook_map: dict[str, str] = {}
        for notebook_id in notebook_ids:
            try:
                notebook = json.loads(nsx.read(notebook_id).decode("utf-8"))
            except (KeyError, json.JSONDecodeError):
                continue
            if isinstance(notebook, dict):
                title = notebook.get("title") or notebook.get("name") or ""
                if title:
                    notebook_map[str(notebook_id)] = str(title)
        return notebook_map

    @staticmethod
    def _is_image(mime_type: str, filename: str) -> bool:
        if mime_type.startswith("image/"):
            return True
        return Path(filename).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

    @staticmethod
    def _guess_mime_type(filename: str) -> str:
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".svg": "image/svg+xml",
        }.get(Path(filename).suffix.lower(), "application/octet-stream")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        result = filename
        for char in '<>:"/\\|?*':
            result = result.replace(char, "_")
        return result
