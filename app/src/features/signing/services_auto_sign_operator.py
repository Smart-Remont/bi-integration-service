from __future__ import annotations

import base64
from typing import Any

import httpx
from loguru import logger
from src.config import mynca_config, workers_config
from src.features.factoring.ff.mynca import MyncaClient, MyncaClientError
from src.service import BaseService

from .helpers import fetch_document_bytes
from .repo import SigningRepository


class AutoSignOperatorService(BaseService):
    """Cron: operator CMS auto-sign via company keys (legacy cronAutoSignOperatorAction)."""

    _SIGN_LEGACY_URL = "https://sign.smartremont.kz/rest/get-sign-info/sign_process_id"

    def __init__(self, repo: SigningRepository, mynca: MyncaClient) -> None:
        self.repo = repo
        self.mynca = mynca

    async def run(self) -> str:
        master_key = mynca_config.nca_master_key.strip()
        if not master_key:
            logger.error("CRON_AUTO_SIGN: NCA_MASTER_KEY is not configured")
            return "0"

        self.mynca.require_configured()

        rows = await self.repo.sign_read_for_auto_sign_operator()
        if not rows:
            logger.info("CRON_AUTO_SIGN: no documents in queue")
            return "0"

        logger.info("CRON_AUTO_SIGN: processing {count} document(s)", count=len(rows))

        for row in rows:
            try:
                await self._process_row(row)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "CRON_AUTO_SIGN: sign_id={sign_id} failed: {error}",
                    sign_id=row.get("sign_id"),
                    error=exc,
                )

        return "0"

    async def _process_row(self, value: dict[str, Any]) -> None:
        sign_id = value.get("sign_id")
        company_id_raw = value.get("company_id")
        company_id = int(company_id_raw) if company_id_raw and int(company_id_raw) > 0 else None
        if company_id is None:
            logger.error("CRON_AUTO_SIGN: company_id missing for sign_id={sign_id}", sign_id=sign_id)
            return

        key_row = await self.repo.company_key_store_get_active_by_company(company_id, mynca_config.nca_master_key)
        if not key_row:
            logger.error(
                "CRON_AUTO_SIGN: no active key for company_id={company_id} sign_id={sign_id}",
                company_id=company_id,
                sign_id=sign_id,
            )
            return

        key_binary = self._key_bytes(key_row.get("key_data"))
        key_password = str(key_row.get("key_password") or "")
        key_b64 = base64.b64encode(key_binary).decode("ascii")

        if not await self.mynca.pkcs12_validate(key_b64=key_b64, password=key_password):
            logger.error(
                "CRON_AUTO_SIGN: invalid certificate company_id={company_id} sign_id={sign_id}",
                company_id=company_id,
                sign_id=sign_id,
            )
            return

        file_b64, ext_id, group_id, insert_ctx = await self._resolve_file(value)
        if not file_b64:
            logger.error("CRON_AUTO_SIGN: empty file for sign_id={sign_id}", sign_id=sign_id)
            return

        file_bytes = base64.b64decode(file_b64)
        sign_result = await self.mynca.cms_sign_save(
            data=file_bytes,
            key_b64=key_b64,
            password=key_password,
            detached=False,
            with_tsp=True,
            ext_id=ext_id or None,
            group_id=str(group_id) if group_id else None,
        )
        sign_process_id = str(sign_result["sign_process_id"])
        dn_name = str(sign_result.get("dn_name") or "")
        response_group_id = sign_result.get("group_id")

        try:
            await self.mynca.download_cms(sign_process_id)
        except MyncaClientError:
            await self._rollback(sign_process_id, reason="download_cms failed")
            return

        new_sign_id = await self.repo.insert_sign_general(
            client_request_id=insert_ctx.get("client_request_id"),
            ds_id=insert_ctx.get("ds_id"),
            client_request_document_id=insert_ctx.get("client_request_document_id"),
            sign_type_code=str(value.get("sign_type_code") or ""),
            sign_message="SIGN_CMS",
            orig_message="SIGN_CMS",
            tsp_message=None,
            dn_name=dn_name,
            sign_what="MYNCA_AUTO",
            sign_pid=value.get("sign_id"),
        )
        if not new_sign_id:
            await self._rollback(sign_process_id, reason="insert_sign_general failed")
            return

        try:
            await self.repo.sign_tab_modify(
                sign_id=new_sign_id,
                sign_process_id=sign_process_id,
                sign_group_id=str(response_group_id) if response_group_id else None,
                sign_method="CMS",
                sign_message=None,
            )
        except Exception:
            await self._rollback(sign_process_id, reason="sign_tab__modify failed")
            return

        logger.info(
            "CRON_AUTO_SIGN: success sign_id={sign_id} new_sign_id={new_sign_id} process_id={process_id}",
            sign_id=sign_id,
            new_sign_id=new_sign_id,
            process_id=sign_process_id,
        )

    async def _resolve_file(
        self,
        value: dict[str, Any],
    ) -> tuple[str, int, str | None, dict[str, object]]:
        insert_ctx: dict[str, object] = {}
        client_sign_process_id = str(value.get("sign_process_id") or "").strip()
        group_id = str(value.get("sign_group_id") or "") or None

        if client_sign_process_id:
            file_b64 = await self.mynca.sign_get_file(client_sign_process_id)
            ext_id = self._ext_id_from_row(value, insert_ctx)
            return file_b64, ext_id, group_id, insert_ctx

        doc_type = str(value.get("doc_type") or "")
        if doc_type == "DS":
            ds_id = int(value["ds_id"])
            insert_ctx["ds_id"] = ds_id
            pdf = await self._fetch_signed_pdf(ds_id, "DS")
            return base64.b64encode(pdf).decode("ascii"), ds_id, group_id, insert_ctx

        if doc_type == "AGREEMENT":
            client_request_id = int(value["agreement_client_request_id"])
            insert_ctx["client_request_id"] = client_request_id
            pdf = await self._fetch_signed_pdf(client_request_id, "AGREEMENT")
            return base64.b64encode(pdf).decode("ascii"), client_request_id, group_id, insert_ctx

        if doc_type == "APP_CLIENT":
            doc_id = int(value["client_request_document_id"])
            insert_ctx["client_request_document_id"] = doc_id
            file_b64 = await self._fetch_app_client_b64(client_sign_process_id or str(value.get("sign_process_id") or ""))
            return file_b64, doc_id, group_id, insert_ctx

        return "", 0, group_id, insert_ctx

    @staticmethod
    def _ext_id_from_row(value: dict[str, Any], insert_ctx: dict[str, object]) -> int:
        doc_type = str(value.get("doc_type") or "")
        if doc_type == "DS" and value.get("ds_id"):
            ds_id = int(value["ds_id"])
            insert_ctx["ds_id"] = ds_id
            return ds_id
        if doc_type == "AGREEMENT" and value.get("agreement_client_request_id"):
            client_request_id = int(value["agreement_client_request_id"])
            insert_ctx["client_request_id"] = client_request_id
            return client_request_id
        if doc_type == "APP_CLIENT" and value.get("client_request_document_id"):
            doc_id = int(value["client_request_document_id"])
            insert_ctx["client_request_document_id"] = doc_id
            return doc_id
        return 0

    async def _fetch_signed_pdf(self, entity_id: int, doc_type: str) -> bytes:
        url = (
            f"{workers_config.partner_api_url}/get_signed_file/"
            f"{entity_id}/{doc_type}/ORIGINAL/"
        )
        return await fetch_document_bytes(url)

    async def _fetch_app_client_b64(self, sign_process_id: str) -> str:
        if not sign_process_id:
            return ""
        url = f"{self._SIGN_LEGACY_URL}/{sign_process_id}"
        timeout = httpx.Timeout(timeout=30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict):
            file_b64 = data.get("sign_file_b64")
            if isinstance(file_b64, str):
                return file_b64
        return ""

    async def _rollback(self, sign_process_id: str, *, reason: str) -> None:
        logger.warning(
            "CRON_AUTO_SIGN: rollback sign_process_id={sign_process_id} reason={reason}",
            sign_process_id=sign_process_id,
            reason=reason,
        )
        try:
            await self.mynca.sign_rollback(sign_process_id)
        except MyncaClientError as exc:
            logger.error("CRON_AUTO_SIGN: rollback failed: {error}", error=exc.detail)

    @staticmethod
    def _key_bytes(raw: object) -> bytes:
        if isinstance(raw, memoryview):
            return raw.tobytes()
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, str):
            if raw.startswith("\\x"):
                return bytes.fromhex(raw[2:])
            return raw.encode("latin-1")
        raise RuntimeError("Unsupported key_data type from DB")
