from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, BinaryIO, TypedDict

from loguru import logger

from src.config import file_store_config, minio_config
from src.storage.minio_client import detect_content_type, put_object
from src.storage.modes import FileStoreMode, build_logical_path, logical_path_to_object_key

FilePayload = bytes | BinaryIO
FileInput = tuple[str, FilePayload] | Any


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


def _validate_mode(mode: str) -> FileStoreMode:
    if not mode:
        raise UnknownFileStoreModeError(mode)
    try:
        return FileStoreMode(mode)
    except ValueError as exc:
        raise UnknownFileStoreModeError(mode) from exc


async def file_store(file: FileInput, mode: str) -> StoredFile:
    """
    Upload a file directly to MinIO (object key `documents/...`).

    Raises:
        UnknownFileStoreModeError: unsupported `mode`
        MinioNotConfiguredError: MINIO_* env is missing
        MinioUploadError: S3 PUT failed
        TypeError: invalid file input
    """
    store_mode = _validate_mode(mode)

    try:
        filename, content = await _normalize_file(file)
    except TypeError:
        raise

    ext = _extension(filename)
    logical_path = build_logical_path(store_mode, ext)
    if logical_path is None:
        raise UnknownFileStoreModeError(mode)

    if not minio_config.is_configured:
        logger.error("MinIO upload requested but MINIO_* env is not configured")
        raise MinioNotConfiguredError

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

    return _stored_file(filename, logical_path, ext)
