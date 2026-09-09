from typing import Any

from src.repository import BaseRepository
from src.repository.base import SpRow, SpRows

from .constants import LANDING_MODULE_CODE, PUBLIC_MODULE_CODE, SALE_MODULE_CODE, UTILS_MODULE_CODE
from .db import scalar_from_sp_rows
from .errors import to_signing_database_error


class SigningRepository(BaseRepository):
    async def did_read_for_signature(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.did_read_for_signature",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def did_read_for_verify(self, did_id: int) -> SpRows:
        try:
            return await self.call_sp(
                "public.did_read_for_verify",
                did_id,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def did_read_for_photo(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.did_read_for_photo",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def did_read_for_detail(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.did_read_for_detail",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def did_get(self, did_id: int) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "public.did_get",
                did_id,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        return rows[0] if rows else None

    async def did_info_get_by_state(self, state: str) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "public.did_info_get_by_state",
                state,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        return rows[0] if rows else None

    async def did_url_get(self, state: str) -> str | None:
        try:
            rows = await self.call_sp(
                "public.did_url_get",
                state,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return str(value)

    async def did_insert(
        self,
        *,
        entity_id: int,
        sign_doc_url: str,
        sign_doc_name: str,
        doc_type: str,
    ) -> int | None:
        try:
            rows = await self.call_sp(
                "public.did_insert",
                entity_id,
                sign_doc_url,
                sign_doc_name,
                doc_type,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def did_upd(self, payload: dict[str, Any]) -> int | None:
        try:
            rows = await self.call_sp(
                "public.did_upd",
                payload.get("did_id"),
                payload.get("signable_id"),
                payload.get("code"),
                payload.get("redirect_url"),
                payload.get("token"),
                payload.get("signature"),
                payload.get("is_valid"),
                payload.get("iin"),
                payload.get("first_name"),
                payload.get("last_name"),
                payload.get("original_xml"),
                payload.get("signed_xml"),
                payload.get("dn_name"),
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def did_error_upd(self, state: str, error: str | None) -> int | None:
        try:
            rows = await self.call_sp(
                "public.did_error_upd",
                state,
                error,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def did_photo_upd(self, did_id: int, photo_url: str) -> int | None:
        try:
            rows = await self.call_sp(
                "public.did_photo_upd",
                did_id,
                photo_url,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def did_detail_insert(self, payload: dict[str, Any]) -> int | None:
        try:
            rows = await self.call_sp(
                "public.did_detail_insert",
                payload["did_id"],
                payload.get("is_ocsp_valid"),
                payload.get("is_tsp_valid"),
                payload.get("is_valid"),
                payload.get("issuer_certificate_dn"),
                payload.get("tsp"),
                payload.get("tsp_start"),
                payload.get("tsp_end"),
                payload.get("full_detail"),
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def ds_get_by_uuid(self, uuid: str) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "ds.ds_get_by_uuid",
                uuid,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        return rows[0] if rows else None

    async def client_request_get_by_uuid(self, uuid: str) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "public.client_request_get_by_uuid",
                uuid,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        return rows[0] if rows else None

    async def sign_read_for_doc(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.sign_read_for_doc",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def sign_group_id_get_by_client_request(self, client_request_id: int) -> str | None:
        try:
            rows = await self.call_sp(
                "public.sign_group_id_get_by_client_request",
                client_request_id,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        if not rows:
            return None
        row = rows[0]
        group_id = row.get("sign_group_id")
        if group_id is None or group_id == "":
            return None
        return str(group_id)

    async def sign_document_upd(
        self,
        *,
        client_request_id: int,
        sign_doc_name: str,
        sign_doc_url: str,
        is_create_task: bool,
        is_update: bool,
    ) -> int | None:
        try:
            rows = await self.call_sp(
                "sale.sign_document_upd",
                client_request_id,
                sign_doc_name,
                sign_doc_url,
                is_create_task,
                is_update,
                module_code=SALE_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def get_client_request_id_by_remont(self, remont_id: int) -> int | None:
        try:
            rows = await self.call_sp(
                "utils.get_client_request_id_by_remont",
                remont_id,
                module_code=UTILS_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def check_iin_sign_client(self, remont_id: int, dn_name: str) -> int | None:
        try:
            rows = await self.call_sp(
                "landing.check_iin_sign_client",
                remont_id,
                dn_name,
                module_code=LANDING_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def cabinet_project_sign__set(
        self,
        *,
        project_remont_id: int,
        sign_process_id: str,
        dn_name: str,
    ) -> None:
        try:
            await self.call_sp(
                "landing.cabinet_project_sign__set",
                project_remont_id,
                sign_process_id,
                dn_name,
                module_code=LANDING_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def cabinet_project_error_sign__clear(
        self,
        *,
        project_remont_id: int,
        sign_process_id: str,
    ) -> None:
        try:
            await self.call_sp(
                "landing.cabinet_project_error_sign__clear",
                project_remont_id,
                sign_process_id,
                module_code=LANDING_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def get_document_type_id_by_code(self, type_code: str) -> int | None:
        try:
            rows = await self.call_sp(
                "utils.get_document_type_id_by_code",
                type_code,
                module_code=UTILS_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def check_iin_sign_third_party_app(
        self,
        client_request_credit_detail_id: int,
        dn_name: str,
    ) -> int | None:
        try:
            rows = await self.call_sp(
                "public.check_iin_sign_third_party_app",
                client_request_credit_detail_id,
                dn_name,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def cr_credit_request_detail__get_info(
        self,
        client_request_credit_detail_id: int,
    ) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "public.cr_credit_request_detail__get_info",
                client_request_credit_detail_id,
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        return rows[0] if rows else None

    async def client_request_upd_doc(
        self,
        *,
        client_request_id: int,
        document_type_id: int,
        document_name: str,
        document_url: str,
        client_receive_date: object | None = None,
        implementation_date: object | None = None,
    ) -> int | None:
        try:
            rows = await self.call_sp(
                "public.client_request_upd_doc",
                0,
                client_request_id,
                document_type_id,
                1255,
                document_name,
                document_url,
                0,
                0,
                None,
                client_receive_date,
                implementation_date,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                0,
                None,
                0,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def cabinet_document_sign_id__set(
        self,
        client_request_document_id: int,
        sign_process_id: str,
        dn_name: str = "",
        sign_group_id: str = "",
    ) -> None:
        try:
            await self.call_sp(
                "landing.cabinet_document_sign_id__set",
                client_request_document_id,
                sign_process_id,
                dn_name,
                sign_group_id,
                module_code=LANDING_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def cr_credit_request__set_doc_id(
        self,
        client_request_credit_detail_id: int,
        client_request_document_id: int,
    ) -> int | None:
        try:
            rows = await self.call_sp(
                "public.cr_credit_request__set_doc_id",
                client_request_credit_detail_id,
                client_request_document_id,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return int(value)

    async def sign_read_for_auto_sign_operator(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.sign_read_for_auto_sign_operator",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

    async def company_key_store_get_active_by_company(
        self,
        company_id: int,
        master_key: str,
    ) -> dict[str, object] | None:
        try:
            rows = await self.call_sp(
                "nca.company_key_store__get_active_by_company",
                company_id,
                master_key,
                cursor=True,
                module_code="MYSPACE",
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        return rows[0] if rows else None

    async def insert_sign_general(
        self,
        *,
        client_request_id: object | None = None,
        ds_id: object | None = None,
        client_request_document_id: object | None = None,
        sign_type_code: str,
        sign_message: str,
        orig_message: str,
        tsp_message: object | None,
        dn_name: str,
        sign_what: str = "MYNCA_AUTO",
        sign_pid: object | None = None,
    ) -> int | None:
        from src.features.payments.constants import CLIENT_MODULE_CODE

        try:
            rows = await self.call_sp(
                "client.insert_sign_general",
                client_request_id,
                ds_id,
                client_request_document_id,
                sign_type_code,
                sign_message,
                orig_message,
                tsp_message,
                dn_name,
                sign_what,
                sign_pid,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        return int(value) if value is not None else None

    async def sign_tab_modify(
        self,
        *,
        sign_id: int,
        sign_process_id: str | None,
        sign_group_id: str | None,
        sign_method: str | None,
        sign_message: str | None,
    ) -> None:
        from src.features.payments.constants import CLIENT_MODULE_CODE

        try:
            await self.call_sp(
                "client.sign_tab__modify",
                sign_id,
                sign_process_id,
                sign_group_id,
                sign_method,
                sign_message,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc
