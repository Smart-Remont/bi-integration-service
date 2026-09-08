from __future__ import annotations

import base64
import mimetypes
from datetime import date
from typing import TYPE_CHECKING

import httpx
from loguru import logger

from src.config import minio_config, mynca_config, signing_config
from src.storage.minio_client import detect_content_type, put_object
from src.storage.modes import logical_path_to_object_key, php_uniqid

from .aitu_client import AituClient
from .constants import AITU_DEFAULT_BASE_URL
from .settings_repo import SigningSettingsRepository

if TYPE_CHECKING:
    from src.features.factoring.ff.mynca import MyncaClient

    from .repo import SigningRepository


async def resolve_aitu_base_url(settings: SigningSettingsRepository) -> str:
    if signing_config.aitu_base_url:
        return signing_config.aitu_base_url.rstrip("/")
    db_val = await settings.get_setting_value_by_code("AITU_BASE_URL")
    if db_val:
        return db_val.rstrip("/")
    return AITU_DEFAULT_BASE_URL


async def build_aitu_client(
    settings: SigningSettingsRepository,
    *,
    extra_scopes: list[str] | None = None,
) -> AituClient:
    base_url = await resolve_aitu_base_url(settings)
    parse_url = signing_config.aitu_parse_url or ""
    if not parse_url:
        db_parse = await settings.get_setting_value_by_code("AITU_PARSE_URL")
        if db_parse:
            parse_url = db_parse
    return AituClient(base_url=base_url, parse_url=parse_url, extra_scopes=extra_scopes)


async def resolve_aitu_credentials(settings: SigningSettingsRepository) -> tuple[str, str, str]:
    client_id = signing_config.aitu_client_id or await settings.get_setting_value_by_code("AITU_CLIENT") or ""
    client_secret = (
        signing_config.aitu_client_secret or await settings.get_setting_value_by_code("AITU_SECRET") or ""
    )
    redirect_url = (
        signing_config.aitu_redirect_url or await settings.get_setting_value_by_code("AITU_REDIRECT_URL") or ""
    )
    return client_id, client_secret, redirect_url


def aitu_basic_auth(client_id: str, client_secret: str) -> str:
    return base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("ascii")


def public_document_url(sign_doc_url: str) -> str:
    base = signing_config.public_base_url.rstrip("/")
    path = sign_doc_url if sign_doc_url.startswith("/") else f"/{sign_doc_url}"
    return f"{base}{path}"


async def fetch_document_bytes(url: str) -> bytes:
    timeout = httpx.Timeout(timeout=60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def docx_bytes_to_pdf_path(
    *,
    doc_bytes: bytes,
    mynca: MyncaClient,
    filename_prefix: str,
) -> tuple[str, bytes]:
    pdf_bytes = await mynca.docx_to_pdf(doc_bytes)
    ext = "pdf"
    logical_path = (
        f"/documents/{date.today().strftime('%Y.%m.%d')}/client_request_docs/"
        f"{filename_prefix}_{php_uniqid()}.{ext}"
    )
    await _store_bytes(logical_path, pdf_bytes, f"{filename_prefix}.{ext}")
    return logical_path, pdf_bytes


async def _store_bytes(logical_path: str, content: bytes, filename: str) -> None:
    if not minio_config.is_configured:
        logger.warning("MinIO not configured — sign_doc_url stored without upload: {}", logical_path)
        return
    object_key = logical_path_to_object_key(logical_path)
    await put_object(
        key=object_key,
        body=content,
        content_type=detect_content_type(filename),
    )


async def read_sign_doc_bytes(sign_doc_url: str) -> bytes:
    if sign_doc_url.startswith("http://") or sign_doc_url.startswith("https://"):
        return await fetch_document_bytes(sign_doc_url)
    return await fetch_document_bytes(public_document_url(sign_doc_url))


async def store_liveness_photo(did_id: int, photo_bytes: bytes) -> str:
    mime, _ = mimetypes.guess_type("photo.jpg")
    ext = "jpg"
    if mime == "image/png":
        ext = "png"
    uniq = php_uniqid(f"did_liveness_{did_id}_")
    logical_path = f"/documents/{date.today().strftime('%Y.%m.%d')}/did_liveness_photos/{uniq}.{ext}"
    await _store_bytes(logical_path, photo_bytes, f"did_liveness.{ext}")
    return logical_path
