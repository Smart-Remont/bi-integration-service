from __future__ import annotations

from src.config import minio_config
from src.features.factoring.ff.mynca import MyncaClient
from src.storage.minio_client import detect_content_type, put_object
from src.storage.modes import FileStoreMode, build_logical_path, logical_path_to_object_key

from .repo import SigningRepository


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

        logical_path = build_logical_path(FileStoreMode.CLIENT_REQUEST_DOC, "pdf")
        if minio_config.is_configured:
            await put_object(
                key=logical_path_to_object_key(logical_path),
                body=pdf_bytes,
                content_type=detect_content_type("contract.pdf"),
            )

        sign_doc_name = f"Договор_оказания_услуг_{client_request_id}.pdf"
        await self.repo.sign_document_upd(
            client_request_id=client_request_id,
            sign_doc_name=sign_doc_name,
            sign_doc_url=logical_path,
            is_create_task=is_create_task,
            is_update=is_update,
        )
