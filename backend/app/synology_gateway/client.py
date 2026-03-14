from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_SESSION_EXPIRED_CODES = frozenset({105, 106, 119})


class SynologyAuthError(Exception):
    def __init__(self, code: int, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or f"Synology authentication failed (code: {code})")


class Synology2FARequiredError(Exception):
    pass


class SynologyApiError(Exception):
    def __init__(self, code: int, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or f"Synology API error (code: {code})")


class SynologyClient:
    def __init__(self, url: str, user: str, password: str) -> None:
        self._url = url.rstrip("/")
        self._user = user
        self._password = password
        self._sid: str | None = None
        settings = get_settings()
        self._client = httpx.AsyncClient(timeout=30.0, verify=settings.SYNOLOGY_VERIFY_SSL)

    async def login(self, otp_code: str | None = None) -> str:
        params: dict[str, str | int] = {
            "api": "SYNO.API.Auth",
            "version": 6,
            "method": "login",
            "account": self._user,
            "passwd": self._password,
            "session": "FileStation",
            "format": "sid",
        }
        if otp_code:
            params["otp_code"] = otp_code
            params["enable_device_token"] = "yes"
        response = await self._client.get(f"{self._url}/webapi/auth.cgi", params=params)
        data = response.json()
        if not data.get("success"):
            code = data.get("error", {}).get("code", 0)
            if code == 403:
                raise Synology2FARequiredError()
            raise SynologyAuthError(code)
        self._sid = str(data["data"]["sid"])
        return self._sid

    async def logout(self) -> None:
        if self._sid is None:
            return
        await self._client.get(
            f"{self._url}/webapi/auth.cgi",
            params={
                "api": "SYNO.API.Auth",
                "version": 6,
                "method": "logout",
                "session": "FileStation",
                "_sid": self._sid,
            },
        )
        self._sid = None

    async def request(self, api: str, method: str, version: int = 1, **params: object) -> dict:
        if self._sid is None:
            await self.login()
        result = await self._raw_request(api, method, version, **params)
        if result.get("success"):
            return result.get("data", {})
        code = result.get("error", {}).get("code", 0)
        if code in _SESSION_EXPIRED_CODES:
            await self.login()
            result = await self._raw_request(api, method, version, **params)
            if result.get("success"):
                return result.get("data", {})
            code = result.get("error", {}).get("code", 0)
        raise SynologyApiError(code)

    async def _raw_request(self, api: str, method: str, version: int, **extra_params: object) -> dict:
        response = await self._client.get(
            f"{self._url}/webapi/entry.cgi",
            params={"api": api, "version": version, "method": method, "_sid": self._sid, **extra_params},
        )
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> SynologyClient:
        await self.login()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.logout()
        await self.close()
