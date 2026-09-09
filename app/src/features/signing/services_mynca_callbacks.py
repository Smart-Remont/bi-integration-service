from __future__ import annotations

from datetime import date
from typing import Any

from loguru import logger
from src.config import mynca_config
from src.service import BaseService

from .errors import SigningDatabaseError
from .repo import SigningRepository


def _str(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _meta(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("meta_data")
    return raw if isinstance(raw, dict) else {}


def _dn_name(payload: dict[str, Any]) -> str:
    dn = _str(payload.get("dn_name"))
    if dn:
        return dn
    signer = payload.get("signer")
    if isinstance(signer, dict):
        subject = signer.get("subject")
        if isinstance(subject, dict):
            return _str(subject.get("dn"))
    return ""


def _ext_id(payload: dict[str, Any]) -> int:
    try:
        return int(payload.get("ext_id") or 0)
    except (TypeError, ValueError):
        return 0


def _is_success(payload: dict[str, Any]) -> bool:
    return _str(payload.get("status")).upper() == "SUCCESS"


def _is_signed_ok(payload: dict[str, Any]) -> bool:
    if "is_signed" not in payload:
        return True
    flag = payload.get("is_signed")
    return flag is True or flag == 1


def mynca_sign_page_url(sign_process_id: str) -> str:
    base = mynca_config.sign_page_url.strip() or "https://nca.smartremont.kz/sign/"
    if not base.endswith("/"):
        base += "/"
    return f"{base}{sign_process_id}"


class MyncaCallbackService(BaseService):
    """Incoming MyNCA back_url handlers (legacy PHP ClientSign + Cabinet)."""

    def __init__(self, repo: SigningRepository) -> None:
        self.repo = repo

    async def client_sign(self, payload: dict[str, Any]) -> dict[str, object]:
        sign_process_id = _str(payload.get("sign_process_id"))
        if not sign_process_id:
            raise RuntimeError("sign_process_id не указан")

        if not _is_success(payload):
            logger.info(
                "mynca client-sign callback ignored status={status} process={pid}",
                status=payload.get("status"),
                pid=sign_process_id,
            )
            return {"status": True}

        meta = _meta(payload)
        type_code = _str(meta.get("type_code"))
        doc_type = _str(meta.get("doc_type")).upper()
        ext_id = _ext_id(payload)

        sign_type_code: str | None = None
        client_request_id: int | None = None
        ds_id: int | None = None
        client_request_document_id: int | None = None

        def _meta_int(key: str) -> int:
            try:
                return int(meta.get(key) or 0)
            except (TypeError, ValueError):
                return 0

        if type_code == "CLIENT_DS_SIGN" or doc_type == "DS":
            sign_type_code = "CLIENT_DS_SIGN"
            ds_id = _meta_int("ds_id") or ext_id
        elif type_code == "OTBASY_STATEMENT_SIGN" or doc_type == "OTBASY_STATEMENT":
            sign_type_code = "OTBASY_STATEMENT_SIGN"
            client_request_document_id = _meta_int("client_request_document_id") or ext_id
        elif type_code == "CLIENT_SIGN" or doc_type == "AGREEMENT":
            sign_type_code = "CLIENT_SIGN"
            client_request_id = _meta_int("client_request_id") or ext_id

        if sign_type_code is None:
            logger.warning(
                "mynca client-sign unknown type_code process={pid} ext_id={ext_id}",
                pid=sign_process_id,
                ext_id=ext_id,
            )
            return {"status": True}

        sign_id = await self.repo.insert_sign_general(
            client_request_id=client_request_id,
            ds_id=ds_id,
            client_request_document_id=client_request_document_id,
            sign_type_code=sign_type_code,
            sign_message="SIGN_CMS",
            orig_message="SIGN_CMS",
            tsp_message=None,
            dn_name=_dn_name(payload),
            sign_what="MYNCA",
            sign_pid=None,
        )
        if not sign_id:
            raise RuntimeError("Ошибка insert_sign_general")

        group_id = _str(payload.get("group_id")) or None
        try:
            await self.repo.sign_tab_modify(
                sign_id=sign_id,
                sign_process_id=sign_process_id,
                sign_group_id=group_id,
                sign_method="CMS",
                sign_message=None,
            )
        except SigningDatabaseError as exc:
            logger.error(
                "mynca client-sign sign_tab__modify failed sign_id={sign_id}: {error}",
                sign_id=sign_id,
                error=exc.message,
            )
        return {"status": True}

    async def project_remont(self, payload: dict[str, Any]) -> dict[str, object]:
        sign_process_id = _str(payload.get("sign_process_id"))
        if not sign_process_id:
            raise RuntimeError("sign_process_id не указан")
        if not _is_success(payload):
            err = _str(payload.get("error")) or f"Статус подписи: {payload.get('status')}"
            raise RuntimeError(err)
        if not _is_signed_ok(payload):
            raise RuntimeError("Документ не подписан")

        ext_id = _ext_id(payload)
        if ext_id <= 0:
            raise RuntimeError("ext_id не указан")

        try:
            await self.repo.cabinet_project_sign__set(
                project_remont_id=ext_id,
                sign_process_id=sign_process_id,
                dn_name=_dn_name(payload),
            )
        except SigningDatabaseError:
            await self.repo.cabinet_project_error_sign__clear(
                project_remont_id=ext_id,
                sign_process_id=sign_process_id,
            )
            raise
        return {"status": True}

    async def cabinet_act(
        self,
        payload: dict[str, Any],
        *,
        document_name: str,
        document_type_code: str,
    ) -> dict[str, object]:
        sign_process_id = _str(payload.get("sign_process_id"))
        sign_group_id = _str(payload.get("group_id"))
        if not sign_process_id:
            raise RuntimeError("sign_process_id не указан")
        if not sign_group_id:
            raise RuntimeError("sign_group_id не указан")
        if not _is_success(payload):
            err = _str(payload.get("error")) or f"Статус подписи: {payload.get('status')}"
            raise RuntimeError(err)
        if not _is_signed_ok(payload):
            raise RuntimeError("Документ не подписан")

        ext_id = _ext_id(payload)
        if ext_id <= 0:
            raise RuntimeError("ext_id не указан")

        dn_name = _dn_name(payload)
        check = await self.repo.check_iin_sign_client(ext_id, dn_name)
        if check is None:
            raise RuntimeError("Проверка ИИН не пройдена")

        doc_type_id = await self.repo.get_document_type_id_by_code(document_type_code)
        if doc_type_id is None:
            raise RuntimeError(f"document_type {document_type_code} не найден")

        client_request_id = await self.repo.get_client_request_id_by_remont(ext_id)
        if client_request_id is None:
            raise RuntimeError("client_request_id не найден")

        today = date.today()
        document_id = await self.repo.client_request_upd_doc(
            client_request_id=client_request_id,
            document_type_id=doc_type_id,
            document_name=document_name,
            document_url=mynca_sign_page_url(sign_process_id),
            client_receive_date=today,
            implementation_date=today,
        )
        if document_id is None:
            raise RuntimeError("Ошибка сохранения документа")

        await self.repo.cabinet_document_sign_id__set(
            document_id,
            sign_process_id,
            dn_name,
            sign_group_id,
        )
        return {"status": True}

    async def app(self, payload: dict[str, Any]) -> dict[str, object]:
        return await self.cabinet_act(
            payload,
            document_name="Акт прием передачи.pdf",
            document_type_code="APART_PASS_ACT_CL",
        )

    async def defect(self, payload: dict[str, Any]) -> dict[str, object]:
        return await self.cabinet_act(
            payload,
            document_name="Дефектный акт.pdf",
            document_type_code="CLIENT_DEFECT_ACT",
        )
