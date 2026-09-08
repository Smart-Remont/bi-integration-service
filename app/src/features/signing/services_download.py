from __future__ import annotations

import base64
from datetime import date

from src.config import minio_config, signing_config
from src.features.factoring.ff.mynca import MyncaClient
from src.storage.minio_client import detect_content_type, put_object
from src.storage.modes import logical_path_to_object_key, php_uniqid

from .helpers import fetch_document_bytes
from .repo import SigningRepository


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
