from src.repository import BaseRepository

from .constants import CRM_MODULE_CODE, PUBLIC_MODULE_CODE
from .errors import to_leads_database_error


class LeadsSettingsRepository(BaseRepository):
    async def get_setting_value_by_code(self, setting_code: str) -> str | None:
        try:
            rows = await self.call_sp(
                "public.get_setting_value_by_code",
                setting_code,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc
        if not rows:
            return None
        return str(next(iter(rows[0].values())))


class LeadsRepository(BaseRepository):
    async def request_from_tilda(self, body_json: str) -> None:
        try:
            await self.call_sp(
                "crm.request_from_tilda",
                body_json,
                module_code=CRM_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc

    async def request_from_fb(self, body_json: str) -> None:
        try:
            await self.call_sp(
                "crm.request_from_fb",
                body_json,
                module_code=CRM_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc

    async def request_from_albato_meta(self, body_json: str) -> int | None:
        try:
            rows = await self.call_sp(
                "crm.request_from_albato_meta",
                body_json,
                module_code=CRM_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc
        if not rows:
            return None
        value = next(iter(rows[0].values()))
        return int(value) if value is not None else None

    async def tilda_setting_get(self, code: str) -> str | None:
        try:
            rows = await self.call_sp(
                "public.tilda_setting_get",
                code,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc
        if not rows:
            return None
        row = rows[0]
        val = row.get("tilda_setting_value")
        return str(val) if val is not None else None

    async def tilda_project_insert(self, body_json: str) -> None:
        try:
            await self.call_sp(
                "public.tilda_project_insert",
                body_json,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc

    async def tilda_project_read(self):
        try:
            return await self.call_sp(
                "public.tilda_project_read",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc

    async def tilda_webhook_insert(
        self,
        *,
        page_id: str,
        project_id: str,
        published: str,
    ) -> None:
        try:
            await self.call_sp(
                "public.tilda_webhook_insert",
                page_id,
                project_id,
                published,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc

    async def tilda_webhook_read(self):
        try:
            return await self.call_sp(
                "public.tilda_webhook_read",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc

    async def tilda_webhook_set_downloaded(self, tilda_webhook_id: int) -> None:
        try:
            await self.call_sp(
                "public.tilda_webhook_set_downloaded",
                tilda_webhook_id,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_leads_database_error(exc) from exc
