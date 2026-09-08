from src.repository import BaseRepository

from .constants import DDU_MODULE_CODE, PUBLIC_MODULE_CODE
from .errors import to_workers_database_error


class WorkersSettingsRepository(BaseRepository):
    async def get_setting_value_by_code(self, setting_code: str) -> str | None:
        try:
            rows = await self.call_sp(
                "public.get_setting_value_by_code",
                setting_code,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc
        if not rows:
            return None
        return str(next(iter(rows[0].values())))


class WorkersRepository(BaseRepository):
    async def flat_upd(self, body_json: str) -> None:
        try:
            await self.call_sp(
                "public.flat_upd",
                body_json,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def resident_for_flat_sync_read(self):
        try:
            return await self.call_sp(
                "public.resident_for_flat_sync_read",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def resident_1c_sync_upd(self, body_json: str) -> None:
        try:
            await self.call_sp(
                "public.resident_1c_sync_upd",
                body_json,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def resident_1c_sync(self, body_json: str) -> None:
        try:
            await self.call_sp(
                "public.resident_1c_sync",
                body_json,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def integration_tab__read(self):
        try:
            return await self.call_sp(
                "public.integration_tab__read",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def integration_tab__set_send(self, integration_id: int, received_json: str) -> None:
        try:
            await self.call_sp(
                "public.integration_tab__set_send",
                integration_id,
                received_json,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def integration_tab__set_error(self, integration_id: int, error: str) -> None:
        try:
            await self.call_sp(
                "public.integration_tab__set_error",
                integration_id,
                error,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def parse_pdf__read_agreement(self):
        try:
            return await self.call_sp(
                "public.parse_pdf__read_agreement",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def parse_pdf__process_agreement(self, sign_id: int, is_ok: str | None) -> None:
        try:
            await self.call_sp(
                "public.parse_pdf__process_agreement",
                sign_id,
                is_ok,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def freedom_token_upd(self, token_json: str) -> None:
        try:
            await self.call_sp(
                "public.freedom_token_upd",
                token_json,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def ddu_cancel_status_read(self):
        try:
            return await self.call_sp(
                "rest.ddu_cancel_status_read",
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def ddu_timeout_request_read(self):
        try:
            return await self.call_sp(
                "rest.ddu_timeout_request_read",
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def ddu_request_to_cancel(self, client_request_id: int, desc: str) -> None:
        try:
            await self.call_sp(
                "rest.ddu_request_to_cancel",
                client_request_id,
                desc,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def ddu_request_reserve_renew(self, client_request_id: int) -> None:
        try:
            await self.call_sp(
                "rest.ddu_request_reserve_renew",
                client_request_id,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    # Planoplan (rest.*)
    async def pp_folder_project_del(self) -> None:
        try:
            await self.call_sp("rest.pp_folder_project_del", module_code=DDU_MODULE_CODE)
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_insert_folder(self, folder_id: int, folder_name: str, resident_name: str) -> None:
        try:
            await self.call_sp(
                "rest.pp_insert_folder",
                folder_id,
                folder_name,
                resident_name,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_insert_project(self, project_id: int, project_name: str, folder_id: int) -> None:
        try:
            await self.call_sp(
                "rest.pp_insert_project",
                project_id,
                project_name,
                folder_id,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_insert_job(self, resident_id: int) -> None:
        try:
            await self.call_sp(
                "rest.pp_insert_job",
                resident_id,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_read_job(self):
        try:
            return await self.call_sp(
                "rest.pp_read_job",
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_job_set_time(self, pp_render_job_id: int, time_type: str) -> None:
        try:
            await self.call_sp(
                "rest.pp_job_set_time",
                pp_render_job_id,
                time_type,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_read_planirovka_by_resident(self, resident_id: int):
        try:
            return await self.call_sp(
                "rest.pp_read_planirovka_by_resident",
                resident_id,
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_planirovka_room_pic_read(self, planirovka_id: int):
        try:
            return await self.call_sp(
                "rest.pp_planirovka_room_pic_read",
                planirovka_id,
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_delete_render(self, planirovka_id: int) -> None:
        try:
            await self.call_sp(
                "rest.pp_delete_render",
                planirovka_id,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_read_project(self, planirovka_id: int):
        try:
            return await self.call_sp(
                "rest.pp_read_project",
                planirovka_id,
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_insert_render(
        self,
        *,
        planirovka_id: int,
        preset_code: str,
        rakurs_url: str,
        room_info: str,
    ) -> None:
        try:
            await self.call_sp(
                "rest.pp_insert_render",
                planirovka_id,
                preset_code,
                rakurs_url,
                room_info,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc

    async def pp_update_planirovka_folder(self, planirovka_id: int, folder_name: str) -> None:
        try:
            await self.call_sp(
                "rest.pp_update_planirovka_folder",
                planirovka_id,
                folder_name,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_workers_database_error(exc) from exc
