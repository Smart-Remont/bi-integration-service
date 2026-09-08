from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Any

import httpx
from loguru import logger
from pypdf import PdfReader

from src.config import minio_config, workers_config
from src.storage.minio_client import detect_content_type, put_object
from src.storage.modes import logical_path_to_object_key, php_uniqid

from .repo import WorkersRepository, WorkersSettingsRepository


class WorkersService:
    def __init__(
        self,
        repo: WorkersRepository,
        settings: WorkersSettingsRepository,
    ) -> None:
        self.repo = repo
        self.settings = settings

    async def flat_list(self, guid: str) -> dict[str, Any]:
        if not guid.strip():
            return {"status": False, "value": None, "error": "GUID не может быть пустым"}
        result_text = await self._bi_placements(guid)
        if not self._is_json(result_text):
            return {"status": False, "value": None, "error": "Invalid JSON"}
        await self.repo.flat_upd(result_text)
        return {"status": True, "value": json.loads(result_text)}

    async def send_bi_process(self) -> str:
        rows = await self.repo.integration_tab__read()
        if not rows:
            return "0"
        auth = self._bi_basic_auth()
        timeout = httpx.Timeout(timeout=60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for value in rows:
                integration_id = int(value["integration_id"])
                try:
                    response = await client.post(
                        workers_config.bi_crm_create_finish_url,
                        content=str(value["sent_json"]),
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Basic {auth}",
                        },
                    )
                    if response.status_code >= 400:
                        await self.repo.integration_tab__set_error(
                            integration_id,
                            json.dumps(response.text),
                        )
                    else:
                        await self.repo.integration_tab__set_send(
                            integration_id,
                            response.text,
                        )
                except Exception as exc:  # noqa: BLE001
                    await self.repo.integration_tab__set_error(
                        integration_id,
                        json.dumps(str(exc)),
                    )
        return "0"

    async def bi_resident_sync(self) -> str:
        auth = self._bi_basic_auth()
        timeout = httpx.Timeout(timeout=120.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                workers_config.bi_residents_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {auth}",
                },
            )
            response.raise_for_status()
            body = response.text
        await self.repo.resident_1c_sync_upd(body)
        await self.repo.resident_1c_sync(body)
        return "0"

    async def flat_sync_auto(self) -> str:
        rows = await self.repo.resident_for_flat_sync_read()
        if not rows:
            return "Пусто"
        for value in rows:
            result = await self._bi_placements(str(value["guid"]))
            if self._is_json(result):
                await self.repo.flat_upd(result)
        return "0"

    async def pdf_find_sum(self) -> str:
        rows = await self.repo.parse_pdf__read_agreement()
        if not rows:
            return "0"
        for value in rows:
            sign_id = int(value["sign_id"])
            url = f"{workers_config.contractor_agreement_pdf_base}/{sign_id}/"
            try:
                timeout = httpx.Timeout(timeout=60.0, connect=10.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    content = response.content
                if not content.startswith(b"%PDF-"):
                    await self.repo.parse_pdf__process_agreement(sign_id, None)
                    continue
                reader = PdfReader(BytesIO(content))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                agreement_sum = float(value["agreement_sum"])
                lower = agreement_sum - 1
                upper = agreement_sum + 1
                pattern = re.compile(
                    rf"\b({self._pattern_number(lower)}|"
                    rf"{self._pattern_number(agreement_sum)}|"
                    rf"{self._pattern_number(upper)})(?:\.\d+)?\b"
                )
                found = False
                for match in pattern.findall(text):
                    num = float(str(match).replace(" ", ""))
                    if lower <= num <= upper:
                        found = True
                        break
                await self.repo.parse_pdf__process_agreement(sign_id, "true" if found else "false")
            except Exception as exc:  # noqa: BLE001
                logger.error("pdf_find_sum sign_id={} err={}", sign_id, exc)
                await self.repo.parse_pdf__process_agreement(sign_id, None)
        return "0"

    async def freedom_auth(self) -> str:
        auth_body = workers_config.freedom_legacy_auth_body
        if not auth_body:
            auth_body = await self.settings.get_setting_value_by_code("FF_AUTH") or ""
        if not auth_body:
            raise RuntimeError("FF_AUTH is not configured")
        url = workers_config.freedom_legacy_base_url.rstrip("/") + "/ffc-api-auth/"
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            response = await client.post(
                url,
                content=auth_body,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()
        if result.get("response"):
            await self.repo.freedom_token_upd(json.dumps(result.get("data")))
        return "0"

    async def freedom_hook(self, raw_body: bytes) -> dict[str, Any]:
        logger.info("FREEDOM_HOOK body={}", raw_body.decode("utf-8", errors="replace"))
        return {"status": True, "value": "OK"}

    async def ddu_request_cancel(self) -> str:
        statuses = await self.repo.ddu_cancel_status_read()
        rows = await self.repo.ddu_timeout_request_read()
        if not rows:
            return "0"

        ipoteka_url = await self.settings.get_setting_value_by_code("BIG_URL_IPOTEKA")
        full_pay_url = await self.settings.get_setting_value_by_code("BIG_URL_FULL_PAY")
        ipoteka_auth = await self.settings.get_setting_value_by_code("BIG_IPOTEKA_BASIC")
        full_pay_auth = await self.settings.get_setting_value_by_code("BIG_FULL_PAY_BASIC")

        for value in rows:
            if value.get("request_type") == "IPOTEKA_SITE" and ipoteka_url and ipoteka_auth:
                payload = json.dumps({"orderId": [value["request_id"]]})
                await self._process_cancel_request(
                    url=ipoteka_url,
                    auth=ipoteka_auth,
                    statuses=statuses,
                    value=value,
                    payload=payload,
                    status_key="statusCode",
                    desc_key="statusDescription",
                )
            elif value.get("request_type") == "FULL_PAY" and full_pay_url and full_pay_auth:
                payload = json.dumps({"applicationIds": [value["request_id"]]})
                await self._process_cancel_request(
                    url=full_pay_url,
                    auth=full_pay_auth,
                    statuses=statuses,
                    value=value,
                    payload=payload,
                    status_key="srStatusCode",
                    desc_key="statusDescription",
                )
        return "0"

    async def render_job_cron(self) -> str:
        lock_path = "/tmp/render_job_cron_status.integrations-sr.lock"
        try:
            from pathlib import Path

            lock_file = Path(lock_path)
            if lock_file.exists():
                return "process is running"
            lock_file.write_text("running", encoding="utf-8")
            try:
                await self.load_folder_project()
                jobs = await self.repo.pp_read_job()
                for job in jobs or []:
                    job_id = int(job["pp_render_job_id"])
                    await self.repo.pp_job_set_time(job_id, "START")
                    residents = await self.repo.pp_read_planirovka_by_resident(int(job["resident_id"]))
                    for resident in residents or []:
                        await self.load_render(int(resident["planirovka_id"]))
                    await self.repo.pp_job_set_time(job_id, "END")
            finally:
                lock_file.unlink(missing_ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.error("render_job_cron error={}", exc)
        return "0"

    async def planoplan(self, planirovka_id: int) -> dict[str, Any]:
        await self.load_render(planirovka_id)
        return {"result": True}

    async def planoplan_mode(self, mode: str, params: dict[str, str]) -> dict[str, Any]:
        if mode == "all_renders":
            resident_id = int(params.get("resident_id") or 0)
            await self.repo.pp_insert_job(resident_id)
            return {"result": {"status": True}}
        if mode == "folders_projects":
            result = await self.load_folder_project()
            return {"result": result}
        return {"result": {"status": False, "error": "Unknown mode"}}

    async def set_folder_name(self, planirovka_id: int, folder_name: str) -> dict[str, Any]:
        await self.repo.pp_update_planirovka_folder(planirovka_id, folder_name)
        return {"result": {"status": True}}

    async def load_folder_project(self) -> dict[str, Any]:
        await self.repo.pp_folder_project_del()
        folders = await self._planoplan_get(f"{workers_config.planoplan_api_base}/folders/")
        for folder in folders.get("value", folders) if isinstance(folders, dict) else folders:
            children = folder.get("children") or []
            for child in children:
                await self.repo.pp_insert_folder(
                    int(child["id"]),
                    str(child["name"]),
                    str(folder["name"]),
                )
        projects_resp = await self._planoplan_get(
            f"{workers_config.planoplan_api_base}/projects/?count=1000000&fields=folder_id"
        )
        items = projects_resp.get("items") if isinstance(projects_resp, dict) else projects_resp
        for project in items or []:
            await self.repo.pp_insert_project(
                int(project["id"]),
                str(project["name"]),
                int(project["folder_id"]),
            )
        return {"status": True}

    async def load_render(self, planirovka_id: int) -> None:
        existing = await self.repo.pp_planirovka_room_pic_read(planirovka_id)
        if existing:
            await self.repo.pp_delete_render(planirovka_id)

        projects = await self.repo.pp_read_project(planirovka_id)
        for project_row in projects or []:
            project_id = project_row["project_id"]
            url = (
                f"{workers_config.planoplan_api_base}/projects/{project_id}"
                "?fields=created, modified, screenshots"
            )
            project = await self._planoplan_get(url)
            project_data = project.get("value", project) if isinstance(project, dict) else project
            preset_code = str(project_data.get("name") or "")
            for shot in project_data.get("screenshots") or []:
                if not shot.get("is_render"):
                    continue
                img_url = shot["file"]
                uniq = php_uniqid(f"{planirovka_id}_")
                logical_path = f"/documents/planoplan/{planirovka_id}/1/{uniq}.jpg"
                timeout = httpx.Timeout(timeout=60.0, connect=10.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(img_url)
                    response.raise_for_status()
                    content = response.content
                if minio_config.is_configured:
                    await put_object(
                        key=logical_path_to_object_key(logical_path),
                        body=content,
                        content_type=detect_content_type(f"{uniq}.jpg"),
                    )
                await self.repo.pp_insert_render(
                    planirovka_id=planirovka_id,
                    preset_code=preset_code,
                    rakurs_url=logical_path,
                    room_info=str(shot.get("cam_info", {}).get("camName") or ""),
                )

    async def _process_cancel_request(
        self,
        *,
        url: str,
        auth: str,
        statuses: list[dict[str, Any]],
        value: dict[str, Any],
        payload: str,
        status_key: str,
        desc_key: str,
    ) -> None:
        timeout = httpx.Timeout(timeout=60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {auth}",
                },
            )
            response.raise_for_status()
            data = response.json()
        first = data[0] if isinstance(data, list) and data else data
        code = first.get(status_key)
        should_cancel = any(s.get("ddu_status_code") == code for s in statuses or [])
        client_request_id = int(value["client_request_id"])
        if should_cancel:
            await self.repo.ddu_request_to_cancel(
                client_request_id,
                str(first.get(desc_key) or ""),
            )
        else:
            await self.repo.ddu_request_reserve_renew(client_request_id)

    async def _bi_placements(self, guid: str) -> str:
        payload = json.dumps(
            {
                "all": True,
                "typeOfRoom": True,
                "blockIds": guid.split(";"),
            }
        )
        auth = self._bi_basic_auth()
        timeout = httpx.Timeout(timeout=120.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                "GET",
                workers_config.bi_placements_url,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {auth}",
                },
            )
            response.raise_for_status()
            return response.text

    async def _planoplan_get(self, url: str) -> Any:
        timeout = httpx.Timeout(timeout=60.0, connect=10.0)
        headers = {"Authorization": f"Bearer {workers_config.planoplan_token}"}
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _bi_basic_auth() -> str:
        user = workers_config.bi_api_user
        password = workers_config.bi_api_password
        return base64.b64encode(f"{user}:{password}".encode()).decode("ascii")

    @staticmethod
    def _is_json(text: str) -> bool:
        try:
            json.loads(text)
            return True
        except json.JSONDecodeError:
            return False

    @staticmethod
    def _pattern_number(number: float) -> str:
        digits = str(int(number))
        return r"\s*".join(digits)
