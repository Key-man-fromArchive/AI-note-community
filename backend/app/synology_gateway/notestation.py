from __future__ import annotations

import html
import re

from app.synology_gateway.client import SynologyClient


class NoteStationService:
    NOTESTATION_API = "SYNO.NoteStation"

    def __init__(self, client: SynologyClient) -> None:
        self._client = client

    async def list_notes(self, offset: int | None = None, limit: int | None = None) -> dict:
        params: dict[str, object] = {}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        return await self._client.request(f"{self.NOTESTATION_API}.Note", "list", version=1, **params)

    async def get_note(self, object_id: str) -> dict:
        return await self._client.request(
            f"{self.NOTESTATION_API}.Note",
            "get",
            version=1,
            object_id=object_id,
        )

    async def list_notebooks(self) -> list[dict]:
        data = await self._client.request(f"{self.NOTESTATION_API}.Notebook", "list", version=1)
        return data.get("notebooks", [])

    @staticmethod
    def extract_text(raw_html: str) -> str:
        if not raw_html.strip():
            return ""
        no_script = re.sub(r"<(script|style)\b.*?</\1>", " ", raw_html, flags=re.IGNORECASE | re.DOTALL)
        with_ocr = re.sub(
            r'<div[^>]*data-type=["\']handwriting-block["\'][^>]*data-ocr-text=["\'](.*?)["\'][^>]*>.*?</div>',
            lambda match: html.unescape(match.group(1)),
            no_script,
            flags=re.IGNORECASE | re.DOTALL,
        )
        text = re.sub(r"<[^>]+>", "\n", with_ocr)
        text = html.unescape(text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()
