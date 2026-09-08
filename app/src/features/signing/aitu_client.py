"""Aitu Passport HTTP client — port of smremont ``Api/AituPassport.php``."""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import urlencode

import httpx
from loguru import logger

from .constants import AITU_DEFAULT_BASE_URL

_DEFAULT_SCOPES = (
    "openid",
    "first_name",
    "last_name",
    "liveness_3d",
    "idpc_verification",
)


class AituClientError(Exception):
    def __init__(self, message: str, *, status_code: int = 502) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AituClient:
    def __init__(
        self,
        *,
        base_url: str = AITU_DEFAULT_BASE_URL,
        parse_url: str = "",
        extra_scopes: list[str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.parse_url = parse_url.rstrip("/") if parse_url else ""
        self.scopes = list(_DEFAULT_SCOPES)
        if extra_scopes:
            self.scopes.extend(extra_scopes)

    def get_redirect_url(
        self,
        client_id: str,
        state: str,
        redirect_url: str,
        phone: str,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": client_id,
            "state": state,
            "redirect_uri": redirect_url,
            "scope": " ".join(self.scopes),
            "phone": phone,
            "theme": "light",
        }
        return f"{self.base_url}/oauth2/auth?{urlencode(params)}"

    @staticmethod
    def response_handler(params: dict[str, Any]) -> dict[str, Any]:
        error_json = json.dumps(params) if "error" in params else None
        return {
            "error_json": error_json,
            "error": params.get("error"),
            "error_description": params.get("error_description"),
            "value": None if "error" in params else params,
            "state": params.get("state"),
            "status": "error" not in params,
        }

    @staticmethod
    def parse_token_id(token: str) -> dict[str, Any]:
        _header, payload, _signature = token.split(".", 2)
        padded = payload + "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded))
        idpc_raw = decoded.get("idpc_verification")
        if isinstance(idpc_raw, str):
            decoded["idpc_verification"] = json.loads(idpc_raw)
        return decoded

    async def get_token(self, data: dict[str, str], basic_auth: str) -> dict[str, Any]:
        form = urlencode(data)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        }
        return await self._post("/api/v1/oauth/token", form, headers, json_body=False)

    async def get_liveness_photo(self, access_token: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        return await self._get("/api/v1/liveness-3d/photo", "", headers, raw_bytes=True)

    async def upload_doc_to_sign(self, data: str, basic_auth: str) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {basic_auth}",
        }
        return await self._post("/api/v2/oauth/signable/xml", data, headers, json_body=False)

    async def get_signatures(self, access_token: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        return await self._get("/api/v2/oauth/signatures/xml", "", headers)

    async def verify_sign(self, data: str, basic_auth: str) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {basic_auth}",
        }
        return await self._post("/api/v2/oauth/signatures/verify", data, headers, json_body=False)

    async def parse_sign(self, data: str) -> dict[str, Any]:
        if not self.parse_url:
            return {
                "status": False,
                "error": "AITU_PARSE_URL is not configured",
                "error_description": None,
                "value": None,
            }
        headers = {"Content-Type": "application/json"}
        return await self._post_external(self.parse_url, data, headers)

    async def _get(
        self,
        path: str,
        query: str,
        headers: dict[str, str],
        *,
        raw_bytes: bool = False,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}{query}"
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                response = await client.get(url, headers=headers)
        except httpx.RequestError as exc:
            logger.error("Aitu GET failed url={url} error={error}", url=url, error=exc)
            return {
                "status": False,
                "error": str(exc),
                "error_description": "Transport error",
                "value": None,
                "code": 0,
            }

        if raw_bytes and response.status_code == 200:
            return {
                "status": True,
                "error": None,
                "error_description": None,
                "value": response.content,
                "code": response.status_code,
            }

        return self._parse_response(response)

    async def _post(
        self,
        path: str,
        data: str,
        headers: dict[str, str],
        *,
        json_body: bool,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                if json_body:
                    response = await client.post(url, content=data, headers=headers)
                else:
                    response = await client.post(url, content=data.encode(), headers=headers)
        except httpx.RequestError as exc:
            logger.error("Aitu POST failed url={url} error={error}", url=url, error=exc)
            return {
                "status": False,
                "error": str(exc),
                "error_description": "Transport error",
                "value": None,
                "code": 0,
            }
        return self._parse_response(response)

    async def _post_external(self, url: str, data: str, headers: dict[str, str]) -> dict[str, Any]:
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                response = await client.post(url, content=data.encode(), headers=headers)
        except httpx.RequestError as exc:
            return {
                "status": False,
                "error": str(exc),
                "error_description": "Transport error",
                "value": None,
                "code": 0,
            }

        result = self._parse_response(response)
        if result["status"] and isinstance(result.get("value"), dict):
            result["value"]["full_detail"] = response.text
        return result

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        code = response.status_code
        try:
            body = response.json()
        except ValueError:
            body = None

        if code != 200:
            error = None
            error_description = None
            if isinstance(body, dict):
                error = body.get("error")
                error_description = body.get("errorDescription") or body.get("error_description")
            return {
                "status": False,
                "error": error,
                "error_description": error_description,
                "value": None,
                "code": code,
            }

        return {
            "status": True,
            "error": None,
            "error_description": None,
            "value": body,
            "code": code,
        }
