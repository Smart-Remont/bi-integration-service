from __future__ import annotations

from typing import TypedDict

from loguru import logger

from src.config import file_store_config, minio_config
from src.storage.minio_client import detect_content_type, put_object
from src.storage.modes import (
    FileStoreMode,
    build_logical_path,
    filename_extension,
    logical_path_to_object_key,
)


class StoredFile(TypedDict):
    filename: str
    path: str
    ext: str
    file_url: str


class UnknownFileStoreModeError(Exception):
    def __init__(self, mode: str) -> None:
        self.mode = mode
        super().__init__(f"Unknown mode: {mode}")


class MinioNotConfiguredError(Exception):
    pass


class MinioUploadError(Exception):
    def __init__(self, mode: str, key: str, cause: Exception) -> None:
        self.mode = mode
        self.key = key
        self.cause = cause
        super().__init__(str(cause))


def _validate_mode(mode: str) -> FileStoreMode:
    if not mode:
        raise UnknownFileStoreModeError(mode)
    try:
        return FileStoreMode(mode)
    except ValueError as exc:
        raise UnknownFileStoreModeError(mode) from exc


async def file_store(filename: str, content: bytes, mode: str) -> StoredFile:
    """
    Upload a file directly to MinIO (object key `documents/...`).

    Raises:
        UnknownFileStoreModeError: unsupported `mode`
        MinioNotConfiguredError: MINIO_* env is missing
        MinioUploadError: S3 PUT failed
    """
    store_mode = _validate_mode(mode)
    if not minio_config.is_configured:
        logger.error("MinIO upload requested but MINIO_* env is not configured")
        raise MinioNotConfiguredError

    ext = filename_extension(filename)
    logical_path = build_logical_path(store_mode, ext)
    object_key = logical_path_to_object_key(logical_path)
    try:
        await put_object(
            key=object_key,
            body=content,
            content_type=detect_content_type(filename),
        )
    except Exception as exc:
        logger.error("file_store MinIO upload failed mode={} key={}: {}", mode, object_key, exc)
        raise MinioUploadError(mode, object_key, exc) from exc

    return {
        "filename": filename,
        "path": logical_path,
        "ext": ext.lower(),
        "file_url": file_store_config.file_url(logical_path),
    }
