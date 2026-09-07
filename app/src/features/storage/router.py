from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from src.config import file_store_config, minio_config
from src.routers.config import api_prefix_config
from src.storage.file_store import file_store
from src.storage.modes import FileStoreMode

from .auth import StorageBasicAuthDep
from .openapi_examples import CONFIG_RESPONSE, MODES_RESPONSE, UPLOAD_RESPONSE
from .schemas import (
    FileStoreConfigResponse,
    FileStoreModesResponse,
    FileUploadResponse,
    build_modes_response,
)

router = APIRouter(prefix=api_prefix_config.v1.storage, tags=["File Storage"])


@router.get(
    "/config",
    response_model=FileStoreConfigResponse,
    summary="Текущая конфигурация хранилища (без секретов)",
    responses={
        200: {
            "description": "Конфигурация backend и MinIO",
            "content": {"application/json": {"example": CONFIG_RESPONSE}},
        },
    },
)
async def get_storage_config(_: StorageBasicAuthDep) -> FileStoreConfigResponse:
    office_ok = bool(file_store_config.base_url and file_store_config.password)
    return FileStoreConfigResponse(
        backend=file_store_config.backend,
        minio_configured=minio_config.is_configured,
        office_proxy_configured=office_ok,
        public_base_url=file_store_config.public_base_url,
        minio_endpoint=minio_config.endpoint or None,
        minio_bucket=minio_config.bucket if minio_config.is_configured else None,
        minio_strict=minio_config.strict,
    )


@router.get(
    "/modes",
    response_model=FileStoreModesResponse,
    summary="Список режимов upload (mode) как в PHP srfileUploadAction",
    description=(
        "Каждый `mode` определяет каталог под `/documents/...` в MinIO "
        "(object key `documents/...`). Контракт совместим с myspace `file_store(mode=...)`."
    ),
    responses={
        200: {
            "description": "Поддерживаемые режимы",
            "content": {"application/json": {"example": MODES_RESPONSE}},
        },
    },
)
async def list_storage_modes(_: StorageBasicAuthDep) -> FileStoreModesResponse:
    return build_modes_response()


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить файл в хранилище",
    description=(
        "## Backend\n\n"
        "| `STORAGE_BACKEND` | Поведение |\n"
        "|---|---|\n"
        "| `office` | Прокси в PHP `/kanban/srfile-upload` (legacy) |\n"
        "| `minio` | Прямой PUT в MinIO (`MINIO_*`, key `documents/...`) |\n"
        "| `dual` | MinIO → при ошибке office proxy (если `MINIO_STRICT=0`) |\n\n"
        "Multipart: поле `file` + form `mode`. Ответ `{filename, path, ext, file_url}` — "
        "как myspace `utils.data_storage.file_store`."
    ),
    responses={
        201: {
            "description": "Файл сохранён",
            "content": {"application/json": {"example": UPLOAD_RESPONSE}},
        },
        400: {"description": "Пустой файл или неизвестный mode"},
        502: {"description": "MinIO/office proxy недоступен или вернул неожиданный ответ"},
        503: {"description": "Хранилище не сконфигурировано"},
    },
)
async def upload_file(
    _: StorageBasicAuthDep,
    file: Annotated[
        UploadFile,
        File(description="Файл для загрузки (аналог PHP `myfiles[]`)"),
    ],
    mode: Annotated[
        FileStoreMode,
        Form(description="Режим каталога — как form `mode` в srfile-upload"),
    ],
) -> FileUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    stored = await file_store((file.filename, content), mode.value)
    if stored is None:
        backend = file_store_config.backend
        if backend == "minio" and not minio_config.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MinIO is not configured (MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY).",
            )
        if backend == "office" and not (file_store_config.base_url and file_store_config.password):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Office file proxy is not configured (FILE_STORE_BASE_URL, FILE_STORE_PASSWORD).",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upload failed for mode={mode.value}",
        )

    return FileUploadResponse.model_validate(stored)
