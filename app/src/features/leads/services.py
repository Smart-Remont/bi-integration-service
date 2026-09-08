from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote_plus, urlencode

import httpx
from loguru import logger

from src.config import leads_config

from .repo import LeadsRepository, LeadsSettingsRepository
from .sanitize import sanitize_lead_tree
from .tilda_client import TildaClient


class LeadsService:
    def __init__(
        self,
        repo: LeadsRepository,
        settings: LeadsSettingsRepository,
    ) -> None:
        self.repo = repo
        self.settings = settings

    async def tilda_form(self, raw_body: bytes) -> str:
        decoded = unquote_plus(raw_body.decode("utf-8", errors="replace"))
        parsed: dict[str, str] = {}
        for key, values in parse_qs(decoded, keep_blank_values=True).items():
            parsed[key] = values[0] if values else ""
        cleaned = sanitize_lead_tree(parsed)
        payload = json.dumps(cleaned, ensure_ascii=False)
        await self.repo.request_from_tilda(payload)
        return "ok"

    async def facebook_form(self, raw_body: bytes) -> str:
        data = json.loads(raw_body.decode("utf-8"))
        cleaned = sanitize_lead_tree(data)
        payload = json.dumps(cleaned, ensure_ascii=False)
        await self.repo.request_from_fb(payload)
        return json.dumps("ok")

    async def albato_meta_lead(self, *, token: str, raw_body: bytes) -> tuple[int, dict[str, Any]]:
        expected = leads_config.albato_meta_token
        if not expected:
            db_token = await self.settings.get_setting_value_by_code("ALBATO_META_TOKEN")
            expected = db_token or ""
        if not expected:
            return 500, {"error": "Не задан токен интеграции"}
        if token != expected:
            return 401, {"error": "Неверный токен"}

        data = json.loads(raw_body.decode("utf-8"))
        if not isinstance(data, dict):
            return 400, {"error": "Пустое или невалидное тело запроса"}
        if not str(data.get("name") or "").strip():
            return 400, {"error": "Поле name обязательно"}
        if not str(data.get("phone") or "").strip():
            return 400, {"error": "Поле phone обязательно"}

        cleaned = sanitize_lead_tree(data)
        payload = json.dumps(cleaned, ensure_ascii=False)
        deal_id = await self.repo.request_from_albato_meta(payload)
        if deal_id is None:
            return 500, {"error": "Не удалось создать лид"}
        return 201, {"status": "ok", "crm_deal_id": deal_id}

    async def image_search(self, query: str) -> list[str]:
        if not query.strip():
            return []
        encoded = urlencode({"q": query, "tbm": "isch"})
        url = f"https://www.google.kz/search?{encoded}"
        timeout = httpx.Timeout(timeout=20.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            html_text = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            html_text.raise_for_status()
            body = html_text.text
        matches = re.findall(r'<img[^>]+src="([^"]+)"', body)
        # Skip first (logo), take next 4 like PHP array_slice after shift
        return matches[1:5] if len(matches) > 1 else matches[:4]

    async def tilda_api_webhook(self, params: dict[str, str]) -> str:
        await self.repo.tilda_webhook_insert(
            page_id=str(params.get("pageid") or params.get("page_id") or ""),
            project_id=str(params.get("projectid") or params.get("project_id") or ""),
            published=str(params.get("published") or ""),
        )
        return "ok"

    async def tilda_project_list_get_projects(self) -> dict[str, Any]:
        client = await self._tilda_client()
        projects = await client.get_projects_list()
        await self.repo.tilda_project_insert(json.dumps(projects, ensure_ascii=False))
        return {"status": True, "value": projects}

    async def tilda_project_list_read(self) -> list[dict[str, Any]]:
        rows = await self.repo.tilda_project_read()
        return list(rows) if rows else []

    async def tilda_project_list(self, mode: str) -> dict[str, Any]:
        if mode == "get_projects":
            return await self.tilda_project_list_get_projects()
        return {"value": await self.tilda_project_list_read()}

    async def tilda_api_export(self, project_id: int) -> dict[str, Any]:
        export_dir = Path(leads_config.tilda_export_dir or "")
        if not export_dir:
            raise RuntimeError("TILDA_EXPORT_DIR is not configured")

        client = await self._tilda_client()
        project = await client.get_project_export(project_id)
        for key in ("export_csspath", "export_jspath", "export_imgpath"):
            if not project.get(key):
                raise RuntimeError(f"Не указана папка {key.replace('export_', '').replace('path', '')}")

        dir_main = export_dir
        dir_css = dir_main / "css"
        dir_js = dir_main / "js"
        dir_img = dir_main / "img"
        for d in (dir_main, dir_css, dir_js, dir_img):
            d.mkdir(parents=True, exist_ok=True)

        await self._download_tilda_assets(project.get("css") or [], dir_css)
        await self._download_tilda_assets(project.get("js") or [], dir_js)
        await self._download_tilda_assets(project.get("images") or [], dir_img, skip_existing=True)

        pages = await client.get_pages_list(project_id)
        for page_meta in pages:
            page = await client.get_page_full_export(page_meta["id"])
            for page_image in page.get("images") or []:
                await self._download_tilda_file(
                    page_image["from"],
                    dir_img / page_image["to"],
                    skip_existing=True,
                )
            html_path = dir_main / page["filename"]
            if page.get("alias"):
                html_path = dir_main / f"{page['alias']}.html"
            if page.get("filename") == "page18450463.html":
                html_path = dir_main / "index.html"
            html_path.write_text(page.get("html") or "", encoding="utf-8")

        return {"status": True, "value": None, "error": None}

    async def tilda_webhook_pages(self) -> str:
        export_dir = Path(leads_config.tilda_export_dir or "")
        if not export_dir:
            logger.warning("TILDA_EXPORT_DIR not set — skip webhook pages export")
            return "0"

        client = await self._tilda_client()
        dir_main = export_dir
        dir_css = dir_main / "css"
        dir_js = dir_main / "js"
        dir_img = dir_main / "img"
        for d in (dir_main, dir_css, dir_js, dir_img):
            d.mkdir(parents=True, exist_ok=True)

        rows = await self.repo.tilda_webhook_read()
        for value in rows or []:
            page = await client.get_page_full_export(value["page_id"])
            for page_image in page.get("images") or []:
                await self._download_tilda_file(
                    page_image["from"],
                    dir_img / page_image["to"],
                    skip_existing=True,
                )
            for css in page.get("css") or []:
                await self._download_tilda_file(css["from"], dir_css / css["to"])
            for js in page.get("js") or []:
                await self._download_tilda_file(js["from"], dir_js / js["to"])
            html_path = dir_main / page["filename"]
            if page.get("alias"):
                html_path = dir_main / f"{page['alias']}.html"
            if page.get("filename") == "page18450463.html":
                html_path = dir_main / "index.html"
            html_path.write_text(page.get("html") or "", encoding="utf-8")
            if value.get("tilda_webhook_id") is not None:
                await self.repo.tilda_webhook_set_downloaded(int(value["tilda_webhook_id"]))
        return "0"

    async def _tilda_client(self) -> TildaClient:
        public = await self.repo.tilda_setting_get("PUBLIC_KEY")
        secret = await self.repo.tilda_setting_get("SECRET_KEY")
        if not public or not secret:
            raise RuntimeError("Tilda PUBLIC_KEY/SECRET_KEY not configured in DB")
        return TildaClient(public, secret)

    async def _download_tilda_assets(
        self,
        items: list[dict[str, str]],
        target_dir: Path,
        *,
        skip_existing: bool = False,
    ) -> None:
        for item in items:
            await self._download_tilda_file(
                item["from"],
                target_dir / item["to"],
                skip_existing=skip_existing,
            )

    async def _download_tilda_file(
        self,
        url: str,
        target: Path,
        *,
        skip_existing: bool = False,
    ) -> None:
        if skip_existing and target.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            target.write_bytes(response.content)
