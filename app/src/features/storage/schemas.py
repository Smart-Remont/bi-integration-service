from pydantic import Field

from src.schema import BaseSchema
from src.storage.modes import FILE_STORE_MODE_DESCRIPTIONS, FileStoreMode

from .openapi_examples import CONFIG_RESPONSE, MODES_RESPONSE, UPLOAD_RESPONSE


class FileUploadResponse(BaseSchema):
    filename: str = Field(description="Исходное имя загруженного файла", examples=["photo.jpg"])
    path: str = Field(
        description="Относительный путь в хранилище (`/documents/...`), как в БД smremont",
        examples=[UPLOAD_RESPONSE["path"]],
    )
    ext: str = Field(description="Расширение файла (lowercase)", examples=["jpg"])
    file_url: str = Field(
        description="Публичный URL: `STORAGE_PUBLIC_URL` + `path`",
        examples=[UPLOAD_RESPONSE["fileUrl"]],
    )


class FileStoreModeItem(BaseSchema):
    mode: FileStoreMode
    description: str = Field(description="Назначение режима")
    path_template: str = Field(description="Шаблон пути (date/uniq — как в PHP srfileUploadAction)")


class FileStoreModesResponse(BaseSchema):
    backend: str = Field(
        description="Текущий `STORAGE_BACKEND`: office | minio | dual",
        examples=["minio"],
    )
    public_base_url: str = Field(
        description="Базовый URL для `file_url`",
        examples=["https://office.smartremont.kz"],
    )
    items: list[FileStoreModeItem]
    total: int


class FileStoreConfigResponse(BaseSchema):
    backend: str = Field(examples=[CONFIG_RESPONSE["backend"]])
    minio_configured: bool = Field(description="Заданы MINIO_ENDPOINT, ACCESS_KEY, SECRET_KEY, BUCKET")
    office_proxy_configured: bool = Field(
        description="Заданы FILE_STORE_BASE_URL (или OFFICE_PUBLIC_URL) и FILE_STORE_PASSWORD"
    )
    public_base_url: str
    minio_endpoint: str | None = Field(default=None, description="MINIO_ENDPOINT (без секретов)")
    minio_bucket: str | None = Field(default=None, description="MINIO_BUCKET")
    minio_strict: bool = Field(description="MINIO_STRICT=1 — без fallback на office proxy в dual")


def build_modes_response() -> FileStoreModesResponse:
    from src.config import file_store_config

    items = [
        FileStoreModeItem(
            mode=mode,
            description=FILE_STORE_MODE_DESCRIPTIONS[mode],
            path_template=_path_template(mode),
        )
        for mode in FileStoreMode
    ]
    return FileStoreModesResponse(
        backend=file_store_config.backend,
        public_base_url=file_store_config.public_base_url,
        items=items,
        total=len(items),
    )


def _path_template(mode: FileStoreMode) -> str:
    templates: dict[FileStoreMode, str] = {
        FileStoreMode.CONTRACTOR_LOGO: "/documents/contractor_logo/contractor_logo_{uniq}.{ext}",
    }
    if mode in templates:
        return templates[mode]
    folder = mode.value.lower()
    return f"/documents/{{date}}/{folder}/{{prefix}}_{{uniq}}.{{ext}}"
