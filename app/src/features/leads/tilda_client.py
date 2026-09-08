"""Minimal Tilda CDN API client — port of ``tilda_php/classes/Tilda/Api.php``."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx


class TildaClient:
    API_URL = "http://api.tildacdn.info/v1/"

    def __init__(self, public_key: str, secret_key: str) -> None:
        self.public_key = public_key
        self.secret_key = secret_key

    async def get_projects_list(self) -> Any:
        return await self._call("getprojectslist", {})

    async def get_project_export(self, project_id: int | str) -> Any:
        return await self._call("getprojectexport", {"projectid": project_id})

    async def get_pages_list(self, project_id: int | str) -> Any:
        return await self._call("getpageslist", {"projectid": project_id})

    async def get_page_full_export(self, page_id: int | str) -> Any:
        return await self._call("getpagefullexport", {"pageid": page_id})

    async def _call(self, method: str, params: dict[str, Any]) -> Any:
        query_params = dict(params)
        query_params["publickey"] = self.public_key
        query_params["secretkey"] = self.secret_key
        url = f"{self.API_URL}{method}/?{urlencode(query_params)}"
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            body = response.json()
        if body.get("status") == "FOUND":
            return body.get("result")
        message = body.get("message") or "Tilda API error"
        raise RuntimeError(message)
