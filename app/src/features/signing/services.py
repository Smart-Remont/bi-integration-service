from __future__ import annotations

import base64
import json
from datetime import date
from typing import TYPE_CHECKING

from loguru import logger

from src.config import minio_config, signing_config
from src.features.factoring.ff.mynca import MyncaClient
from src.storage.modes import FileStoreMode, build_logical_path, php_uniqid

from .helpers import (
    aitu_basic_auth,
    build_aitu_client,
    docx_bytes_to_pdf_path,
    fetch_document_bytes,
    read_sign_doc_bytes,
    resolve_aitu_credentials,
    store_liveness_photo,
)
from .repo import SigningRepository
from .settings_repo import SigningSettingsRepository
from .x509 import parse_x509_sign

if TYPE_CHECKING:
    pass


class SignDocumentService:
    """Port of ``Integration.php::sign_document_upd`` — MyNCA group PDF → MinIO → ``sale.sign_document_upd``."""

    def __init__(
        self,
        repo: SigningRepository,
        mynca: MyncaClient,
    ) -> None:
        self.repo = repo
        self.mynca = mynca

    async def sign_document_upd(
        self,
        client_request_id: int,
        *,
        is_create_task: bool,
        is_update: bool,
    ) -> None:
        sign_group_id = await self.repo.sign_group_id_get_by_client_request(client_request_id)
        if not sign_group_id:
            raise RuntimeError(
                f"sign_group_id отсутствует для client_request_id={client_request_id}"
            )

        self.mynca.require_configured()
        pdf_bytes = await self.mynca.sign_group_download_pdf(sign_group_id)

        ext = "pdf"
        logical_path = build_logical_path(FileStoreMode.CLIENT_REQUEST_DOC, ext)
        from src.config import minio_config
        from src.storage.minio_client import detect_content_type, put_object
        from src.storage.modes import logical_path_to_object_key

        if minio_config.is_configured:
            await put_object(
                key=logical_path_to_object_key(logical_path),
                body=pdf_bytes,
                content_type=detect_content_type(f"contract.{ext}"),
            )

        sign_doc_name = f"Договор_оказания_услуг_{client_request_id}.{ext}"
        await self.repo.sign_document_upd(
            client_request_id=client_request_id,
            sign_doc_name=sign_doc_name,
            sign_doc_url=logical_path,
            is_create_task=is_create_task,
            is_update=is_update,
        )


class AituFlowService:
    """Aitu OAuth redirect flow + perform DS/Agreement sign."""

    def __init__(
        self,
        repo: SigningRepository,
        settings: SigningSettingsRepository,
        mynca: MyncaClient,
    ) -> None:
        self.repo = repo
        self.settings = settings
        self.mynca = mynca

    async def perform_ds_did_sign(self, uuid: str) -> str:
        row = await self.repo.ds_get_by_uuid(uuid)
        if row is None:
            raise RuntimeError("ДС не найден")

        ds_type_code = row.get("ds_type_code")
        office = signing_config.public_base_url.rstrip("/")
        myspace = signing_config.myspace_api_url.rstrip("/")

        if ds_type_code == "AGREEMENT_BARTER":
            doc_url = f"{office}/dict/report/mode/ds_agreement_barter/ds_id/{row['ds_id']}/doc/1"
        elif ds_type_code == "ROOM_CHANGE":
            doc_url = (
                f"{myspace}/client_request/{row['client_request_id']}/ds/{row['ds_id']}"
                "/document/download/?is_sign=true"
            )
        else:
            doc_url = (
                f"{office}/dict/ds-download/is_pdf/false/for_view/false/ds_id/{row['ds_id']}"
                f"/client_request_id/{row['client_request_id']}"
            )

        doc_bytes = await fetch_document_bytes(doc_url)
        sign_doc_url, _pdf = await docx_bytes_to_pdf_path(
            doc_bytes=doc_bytes,
            mynca=self.mynca,
            filename_prefix=f"ds_{row['ds_id']}",
        )
        did_id = await self.repo.did_insert(
            entity_id=int(row["ds_id"]),
            sign_doc_url=sign_doc_url,
            sign_doc_name=f"Доп_соглашение_{row['ds_id']}.pdf",
            doc_type="DS",
        )
        if did_id is None:
            raise RuntimeError("did_insert failed")
        result = await self._aitu_process(did_id, str(row.get("prop_phone") or ""))
        url = result.get("url")
        if not url:
            raise RuntimeError(str(result.get("error") or "aituProcess failed"))
        return str(url)

    async def perform_agreement_did_sign(self, uuid: str) -> str:
        row = await self.repo.client_request_get_by_uuid(uuid)
        if row is None:
            raise RuntimeError("Заявка не найдена")

        office = signing_config.public_base_url.rstrip("/")
        doc_url = (
            f"{office}/dict/report/mode/contract/is_pdf/false/for_view/false/"
            f"client_request_id/{row['client_request_id']}"
        )
        doc_bytes = await fetch_document_bytes(doc_url)
        sign_doc_url, _pdf = await docx_bytes_to_pdf_path(
            doc_bytes=doc_bytes,
            mynca=self.mynca,
            filename_prefix=f"agreement_{row['client_request_id']}",
        )
        did_id = await self.repo.did_insert(
            entity_id=int(row["client_request_id"]),
            sign_doc_url=sign_doc_url,
            sign_doc_name=f"Договор_оказания_услуг_{row['client_request_id']}.pdf",
            doc_type="AGREEMENT",
        )
        if did_id is None:
            raise RuntimeError("did_insert failed")
        result = await self._aitu_process(did_id, str(row.get("prop_phone") or ""))
        url = result.get("url")
        if not url:
            raise RuntimeError(str(result.get("error") or "aituProcess failed"))
        return str(url)

    async def _aitu_process(self, did_id: int, prop_phone: str) -> dict[str, object]:
        did = await self.repo.did_get(did_id)
        if did is None:
            return {"status": False, "error": "did_get failed"}

        client_id, client_secret, redirect_url = await resolve_aitu_credentials(self.settings)
        basic = aitu_basic_auth(client_id, client_secret)
        api = await build_aitu_client(self.settings)

        pdf_bytes = await read_sign_doc_bytes(str(did["sign_doc_url"]))
        xml_inner = (
            '<?xml version="1.0" encoding="UTF-8"?><node><str>'
            + base64.b64encode(pdf_bytes).decode("ascii")
            + "</str></node>"
        )
        original_xml = xml_inner
        convert = base64.b64encode(xml_inner.encode()).decode("ascii")

        upload_payload = json.dumps({"bytes": convert, "name": did["sign_doc_name"]})
        result = await api.upload_doc_to_sign(upload_payload, basic)
        if not result["status"]:
            logger.error("Aitu upload_doc_to_sign failed: {}", result)
            return {"status": False, "error": result.get("error") or "upload failed"}

        signable_id = result["value"]["signableId"]
        api.scopes.append(f"sign.{signable_id}")
        redirect = api.get_redirect_url(client_id, str(did["state"]), redirect_url, prop_phone)

        await self.repo.did_upd(
            {
                "did_id": did_id,
                "signable_id": signable_id,
                "redirect_url": redirect,
                "original_xml": original_xml,
            }
        )
        return {"status": True, "url": redirect}


class SigningCronService:
    def __init__(
        self,
        repo: SigningRepository,
        settings: SigningSettingsRepository,
        mynca: MyncaClient,
    ) -> None:
        self.repo = repo
        self.settings = settings
        self.mynca = mynca
        self.sign_doc = SignDocumentService(repo, mynca)

    async def aitu_get_signs(self) -> str:
        rows = await self.repo.did_read_for_signature()
        if not rows:
            return "0"

        api = await build_aitu_client(self.settings)
        for value in rows:
            token = value.get("token")
            if not token:
                continue
            result = await api.get_signatures(str(token))
            if not result["status"] or not isinstance(result["value"], list):
                continue
            for sign in result["value"]:
                if value.get("signable_id") != sign.get("signableId"):
                    continue
                signed_xml_raw = base64.b64decode(sign["signedXml"]).decode("utf-8", errors="replace")
                parsed = parse_x509_sign(signed_xml_raw)
                if not parsed.get("status"):
                    logger.error("parse_x509_sign failed did_id={}", value.get("did_id"))
                    return "0"
                await self.repo.did_upd(
                    {
                        "did_id": value["did_id"],
                        "signature": sign["signedXml"],
                        "signed_xml": parsed["signed_xml"],
                        "dn_name": parsed["dn_name"],
                    }
                )
        return "0"

    async def aitu_validate_signs(self, did_id: int) -> str:
        rows = await self.repo.did_read_for_verify(did_id)
        if not rows:
            return "0"

        client_id, client_secret, _redirect = await resolve_aitu_credentials(self.settings)
        basic = aitu_basic_auth(client_id, client_secret)
        api = await build_aitu_client(self.settings)

        for value in rows:
            sign_doc_url = value.get("sign_doc_url")
            signature = value.get("signature")
            if not sign_doc_url or not signature:
                continue
            try:
                doc_bytes = await read_sign_doc_bytes(str(sign_doc_url))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skip verify did_id={} err={}", value.get("did_id"), exc)
                continue

            payload = json.dumps(
                {
                    "document": base64.b64encode(doc_bytes).decode("ascii"),
                    "signature": signature,
                }
            )
            result = await api.verify_sign(payload, basic)
            if result["status"] and isinstance(result["value"], dict):
                await self.repo.did_upd(
                    {
                        "did_id": value["did_id"],
                        "is_valid": result["value"].get("valid"),
                    }
                )
        return "0"

    async def aitu_get_photos(self) -> str:
        rows = await self.repo.did_read_for_photo()
        if not rows:
            return "0"

        api = await build_aitu_client(self.settings)
        for value in rows:
            token = value.get("token")
            if not token:
                continue
            result = await api.get_liveness_photo(str(token))
            if result["status"] and isinstance(result["value"], bytes):
                photo_url = await store_liveness_photo(int(value["did_id"]), result["value"])
                await self.repo.did_photo_upd(int(value["did_id"]), photo_url)
        return "0"

    async def aitu_sign_detail(self) -> str:
        rows = await self.repo.did_read_for_detail()
        if not rows:
            return "0"

        api = await build_aitu_client(self.settings)
        for value in rows:
            sign_doc_url = value.get("sign_doc_url")
            signature = value.get("signature")
            if not sign_doc_url or not signature:
                continue
            try:
                doc_bytes = await read_sign_doc_bytes(str(sign_doc_url))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skip sign detail did_id={} err={}", value.get("did_id"), exc)
                continue

            payload = json.dumps(
                {
                    "document": base64.b64encode(doc_bytes).decode("ascii"),
                    "signature": signature,
                }
            )
            result = await api.parse_sign(payload)
            if not result["status"] or not isinstance(result["value"], dict):
                continue
            parsed = result["value"]
            await self.repo.did_detail_insert(
                {
                    "did_id": value["did_id"],
                    "is_ocsp_valid": parsed.get("isOcspValid"),
                    "is_tsp_valid": parsed.get("isTspValid"),
                    "is_valid": parsed.get("isValid"),
                    "issuer_certificate_dn": parsed.get("issuerCertificateDn"),
                    "tsp": parsed.get("tsp"),
                    "tsp_start": parsed.get("tspStart"),
                    "tsp_end": parsed.get("tspEnd"),
                    "full_detail": parsed.get("full_detail"),
                }
            )
        return "0"

    async def cron_auto_upload_sign_doc(self) -> str:
        rows = await self.repo.sign_read_for_doc()
        if not rows:
            return "0"

        for value in rows:
            client_request_id = int(value["agreement_client_request_id"])
            sign_cnt = int(value["sign_cnt"])
            is_create_task = sign_cnt == 1
            is_update = sign_cnt == 2
            try:
                await self.sign_doc.sign_document_upd(
                    client_request_id,
                    is_create_task=is_create_task,
                    is_update=is_update,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "CRON_AUTO_UPLOAD client_request_id={} error={}",
                    client_request_id,
                    exc,
                )
        return "0"


class AituRedirectService:
    def __init__(self, repo: SigningRepository, settings: SigningSettingsRepository) -> None:
        self.repo = repo
        self.settings = settings

    async def handle_approve(self, params: dict[str, str]) -> dict[str, object]:
        from .aitu_client import AituClient

        api = await build_aitu_client(self.settings)
        handled = AituClient.response_handler(params)
        if not handled["status"]:
            if handled.get("state"):
                await self.repo.did_error_upd(str(handled["state"]), handled.get("error_json"))
            return {"ok": False, "error": handled.get("error"), "state": handled.get("state")}

        state = str(handled["state"])
        row = await self.repo.did_info_get_by_state(state)
        if row is None:
            return {"ok": False, "error": "DID not found", "state": state}

        client_id, client_secret, redirect_url = await resolve_aitu_credentials(self.settings)
        basic = aitu_basic_auth(client_id, client_secret)

        token_data = {
            "grant_type": "authorization_code",
            "code": handled["value"]["code"],
            "redirect_uri": redirect_url,
        }
        token_result = await api.get_token(token_data, basic)
        if not token_result["status"]:
            await self.repo.did_error_upd(state, str(token_result.get("error")))
            return {"ok": False, "error": token_result.get("error"), "state": state}

        token = row.get("token")
        if token is None:
            token = token_result["value"]["access_token"]
        id_data = AituClient.parse_token_id(token_result["value"]["id_token"])
        iin = id_data["idpc_verification"]["iin"]
        first_name = id_data.get("first_name")
        last_name = id_data.get("last_name")

        sig_result = await api.get_signatures(str(token) if token else "")
        if not sig_result["status"]:
            err = json.dumps({"error": sig_result.get("error"), "error_description": None})
            await self.repo.did_error_upd(state, err)
            return {"ok": False, "error": sig_result.get("error"), "state": state}

        signed_xml_raw = base64.b64decode(sig_result["value"][0]["signedXml"]).decode(
            "utf-8", errors="replace"
        )
        parsed = parse_x509_sign(signed_xml_raw)
        if not parsed.get("status"):
            return {"ok": False, "error": parsed.get("error"), "state": state}

        await self.repo.did_upd(
            {
                "did_id": row["did_id"],
                "code": handled["value"]["code"],
                "token": token,
                "iin": iin,
                "first_name": first_name,
                "last_name": last_name,
                "signature": sig_result["value"][0]["signedXml"],
                "signed_xml": parsed["signed_xml"],
                "dn_name": parsed["dn_name"],
            }
        )
        return {"ok": True, "state": state}


class SigningDownloadService:
    """PDF download proxy — unsigned via office/myspace + MyNCA; signed via partner API."""

    def __init__(
        self,
        repo: SigningRepository,
        mynca: MyncaClient,
    ) -> None:
        self.repo = repo
        self.mynca = mynca

    async def download_ds(
        self,
        uuid: str,
        *,
        for_view: bool,
        is_base64: bool,
    ) -> tuple[bytes, str] | str:
        row = await self.repo.ds_get_by_uuid(uuid)
        if row is None:
            raise RuntimeError("ДС не найден")
        if row.get("signed"):
            pdf = await self._fetch_signed_pdf(int(row["ds_id"]), "DS", "SIGNED")
            return self._format_output(pdf, "Доп_соглашение.pdf", is_base64)

        doc_url = self._ds_doc_url(row, for_view=for_view)
        doc_bytes = await fetch_document_bytes(doc_url)
        pdf_bytes = await self.mynca.docx_to_pdf(doc_bytes)
        return self._format_output(pdf_bytes, f"ds_{row['ds_id']}.pdf", is_base64)

    async def download_agreement(
        self,
        uuid: str,
        *,
        for_view: bool,
        is_base64: bool,
    ) -> tuple[bytes, str] | str:
        row = await self.repo.client_request_get_by_uuid(uuid)
        if row is None:
            raise RuntimeError("Заявка не найдена")
        if row.get("signed"):
            pdf = await self._fetch_signed_pdf(int(row["client_request_id"]), "AGREEMENT", "SIGNED")
            return self._format_output(pdf, "Подписанный документ.pdf", is_base64)

        office = signing_config.public_base_url.rstrip("/")
        for_view_str = "true" if for_view else "false"
        doc_url = (
            f"{office}/dict/report/mode/contract/is_pdf/false/for_view/{for_view_str}"
            f"/client_request_id/{row['client_request_id']}"
        )
        doc_bytes = await fetch_document_bytes(doc_url)
        pdf_bytes = await self.mynca.docx_to_pdf(doc_bytes)
        return self._format_output(pdf_bytes, f"contract_{row['client_request_id']}.pdf", is_base64)

    def _ds_doc_url(self, row: dict, *, for_view: bool) -> str:
        ds_type_code = row.get("ds_type_code")
        office = signing_config.public_base_url.rstrip("/")
        myspace = signing_config.myspace_api_url.rstrip("/")
        if ds_type_code == "AGREEMENT_BARTER":
            return f"{office}/dict/report/mode/ds_agreement_barter/ds_id/{row['ds_id']}/doc/1"
        if ds_type_code == "ROOM_CHANGE":
            suffix = "" if for_view else "?is_sign=true"
            return (
                f"{myspace}/client_request/{row['client_request_id']}/ds/{row['ds_id']}"
                f"/document/download/{suffix}"
            )
        for_view_str = "true" if for_view else "false"
        return (
            f"{office}/dict/ds-download/for_view/{for_view_str}/ds_id/{row['ds_id']}"
            f"/client_request_id/{row['client_request_id']}"
        )

    async def _fetch_signed_pdf(self, entity_id: int, doc_type: str, sign_type: str) -> bytes:
        from src.config import workers_config

        url = (
            f"{workers_config.partner_api_url}/get_signed_file/"
            f"{entity_id}/{doc_type}/{sign_type}/"
        )
        return await fetch_document_bytes(url)

    @staticmethod
    def _format_output(
        pdf_bytes: bytes,
        filename: str,
        is_base64: bool,
    ) -> tuple[bytes, str] | str:
        if is_base64:
            return base64.b64encode(pdf_bytes).decode("ascii")
        return pdf_bytes, filename


class ThirdPartySignService:
    """Callback from third-party signing app (React Cabinet)."""

    def __init__(self, repo: SigningRepository) -> None:
        self.repo = repo

    async def handle(self, params: dict[str, str]) -> dict[str, object]:
        credit_detail_id = int(params.get("id") or 0)
        dn_name = params.get("dn_name") or ""
        sign_process_id = params.get("sign_process_id") or ""
        signed_xml_b64 = params.get("signed_xml") or ""

        if not credit_detail_id or not dn_name or not sign_process_id or not signed_xml_b64:
            raise RuntimeError("Недостаточно параметров")

        check_id = await self.repo.check_iin_sign_third_party_app(credit_detail_id, dn_name)
        if check_id is None:
            raise RuntimeError("Проверка ИИН не пройдена")

        pdf_bytes = self._extract_pdf_from_signed_xml(signed_xml_b64)
        logical_path = (
            f"/documents/{date.today().strftime('%Y.%m.%d')}/client_request_docs/"
            f"{php_uniqid('third_party_app_doc_')}.pdf"
        )
        from src.storage.minio_client import detect_content_type, put_object
        from src.storage.modes import logical_path_to_object_key

        if minio_config.is_configured:
            await put_object(
                key=logical_path_to_object_key(logical_path),
                body=pdf_bytes,
                content_type=detect_content_type("doc.pdf"),
            )

        row_info = await self.repo.cr_credit_request_detail__get_info(credit_detail_id)
        if row_info is None:
            raise RuntimeError("Данные не найдены")

        doc_type_id = await self.repo.get_document_type_id_by_code("CREDIT_REQUEST")
        if doc_type_id is None:
            raise RuntimeError("document_type CREDIT_REQUEST не найден")

        client_request_document_id = await self.repo.client_request_upd_doc(
            client_request_id=int(row_info["client_request_id"]),
            document_type_id=doc_type_id,
            document_name="Заявление на 3-е лицо.pdf",
            document_url=logical_path,
        )
        if client_request_document_id is None:
            raise RuntimeError("Ошибка сохранения документа")

        await self.repo.cabinet_document_sign_id__set(
            client_request_document_id,
            sign_process_id,
            dn_name,
            "",
        )
        set_id = await self.repo.cr_credit_request__set_doc_id(
            credit_detail_id,
            client_request_document_id,
        )
        if set_id is None:
            raise RuntimeError("Ошибка привязки документа к заявке")

        return {"status": True, "value": None, "error": None}

    @staticmethod
    def _extract_pdf_from_signed_xml(signed_xml_b64: str) -> bytes:
        import xml.etree.ElementTree as ET

        xml_string = base64.b64decode(signed_xml_b64)
        root = ET.fromstring(xml_string)
        pdf_node = root.find("str")
        if pdf_node is None or not pdf_node.text:
            raise RuntimeError("Ошибка при загрузке XML")
        pdf_content = base64.b64decode(pdf_node.text)
        if not pdf_content:
            raise RuntimeError("Ошибка при декодировании PDF")
        return pdf_content
