from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, BinaryIO, TypedDict

import httpx
from loguru import logger

from src.config import file_store_config, minio_config
from src.storage.minio_client import detect_content_type, put_object
from src.storage.modes import build_logical_path, logical_path_to_object_key

FilePayload = bytes | BinaryIO
FileInput = tuple[str, FilePayload] | Any


class StoredFile(TypedDict):
    filename: str
    path: str
    ext: str
    file_url: str


async def _read_bytes(read) -> bytes:
    content = read()
    if hasattr(content, "__await__"):
        content = await content
    if not isinstance(content, bytes):
        raise TypeError("File read() must return bytes")
    return content


async def _normalize_file(file: FileInput) -> tuple[str, bytes]:
    if isinstance(file, tuple):
        name, payload = file
        if isinstance(payload, bytes):
            return name, payload
        if hasattr(payload, "read"):
            return name, await _read_bytes(payload.read)
        raise TypeError("Unsupported file payload type in tuple")

    filename = getattr(file, "filename", None) or getattr(file, "name", None) or "file"
    if not hasattr(file, "read"):
        raise TypeError("Unsupported file input: expected UploadFile or (name, bytes) tuple")
    return filename, await _read_bytes(file.read)


def _extension(filename: str) -> str:
    ext = PurePosixPath(filename).suffix.lstrip(".").lower()
    return ext


def _stored_file(original_filename: str, logical_path: str, ext: str) -> StoredFile:
    return {
        "filename": original_filename,
        "path": logical_path,
        "ext": ext,
        "file_url": file_store_config.file_url(logical_path),
    }


async def _file_store_minio(original_filename: str, content: bytes, mode: str) -> StoredFile | None:
    ext = _extension(original_filename)
    logical_path = build_logical_path(mode, ext)
    if logical_path is None:
        logger.warning("file_store unknown mode for MinIO: {}", mode)
        return None

    if not minio_config.is_configured:
        logger.error("MinIO upload requested but MINIO_* env is not configured")
        return None

    object_key = logical_path_to_object_key(logical_path)
    try:
        await put_object(
            key=object_key,
            body=content,
            content_type=detect_content_type(original_filename),
        )
    except Exception as exc:
        logger.error("file_store MinIO upload failed mode={} key={}: {}", mode, object_key, exc)
        if minio_config.strict:
            raise
        return None

    return _stored_file(original_filename, logical_path, ext)


async def _file_store_office(file: FileInput, mode: str) -> StoredFile | None:
    base_url = file_store_config.base_url.strip()
    password = file_store_config.password
    if not base_url or not password:
        logger.error(
            "file_store office proxy is not configured "
            "(FILE_STORE_BASE_URL/OFFICE_PUBLIC_URL and FILE_STORE_PASSWORD are required)"
        )
        return None

    try:
        filename, content = await _normalize_file(file)
    except TypeError as exc:
        logger.error("file_store invalid file input: {}", exc)
        return None

    upload_url = file_store_config.upload_url
    try:
        async with httpx.AsyncClient(timeout=file_store_config.timeout_seconds) as client:
            response = await client.post(
                upload_url,
                data={"mode": mode},
                files={"myfiles[]": (filename, content)},
                auth=(file_store_config.username, password),
            )
            response.raise_for_status()
            parsed = _parse_office_response(response.json())
            if parsed is None:
                logger.error(
                    "file_store unexpected office response from {}: {}",
                    upload_url,
                    response.text[:500],
                )
                return None
            parsed["file_url"] = file_store_config.file_url(parsed["path"])
            return parsed
    except httpx.HTTPError as exc:
        logger.error("file_store HTTP error for mode={} url={}: {}", mode, upload_url, exc)
        return None
    except ValueError as exc:
        logger.error("file_store invalid JSON from {}: {}", upload_url, exc)
        return None


def _parse_office_response(data: object) -> StoredFile | None:
    item: dict[str, object] | None = None
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            item = first
    elif isinstance(data, dict):
        item = data

    if item and item.get("path"):
        return {
            "filename": str(item.get("filename") or ""),
            "path": str(item["path"]),
            "ext": str(item.get("ext") or ""),
            "file_url": "",
        }
    return None


async def file_store(file: FileInput, mode: str) -> StoredFile | None:
    """
    Upload a file to Smart Remont storage.

    Backend (`STORAGE_BACKEND`, same semantics as smremont `minio.storage_backend`):
    - `office` — HTTP proxy to PHP `/kanban/srfile-upload` (legacy)
    - `minio`  — direct MinIO PUT (`documents/...` key, like `Api_MinioStorage::putFileAs`)
    - `dual`   — MinIO first, fallback to office unless `MINIO_STRICT=1`

    Returns `{filename, path, ext, file_url}` compatible with myspace `file_store()`.
    """
    if not mode:
        logger.warning("file_store called without mode")
        return None

    backend = file_store_config.backend
    if backend not in {"office", "minio", "dual"}:
        logger.error("file_store invalid STORAGE_BACKEND={}", backend)
        return None

    if backend in {"minio", "dual"}:
        try:
            filename, content = await _normalize_file(file)
        except TypeError as exc:
            logger.error("file_store invalid file input: {}", exc)
            return None

        stored = await _file_store_minio(filename, content, mode)
        if stored is not None:
            return stored
        if backend == "minio":
            return None

    if backend in {"office", "dual"}:
        return await _file_store_office(file, mode)

    return None
