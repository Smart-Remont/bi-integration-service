from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import uuid4


class FileStoreMode(StrEnum):
    """Modes supported by `KanbanController::srfileUploadAction` (smremont)."""

    CARD_FILES = "CARD_FILES"
    MASTER_FILES = "MASTER_FILES"
    CHAT_FILES = "CHAT_FILES"
    CHAT_FILES_MINI = "CHAT_FILES_MINI"
    RECIPIENT_FILES = "RECIPIENT_FILES"
    CLIENT_AGREEMENT = "CLIENT_AGREEMENT"
    FLAT_LIST = "FLAT_LIST"
    REMONT_INDICATOR = "REMONT_INDICATOR"
    REQUEST_DOCS = "REQUEST_DOCS"
    MATERIAL_DOCS = "MATERIAL_DOCS"
    PLANIROVKA_PHOTOS = "PLANIROVKA_PHOTOS"
    FINANCE_PAYMENT = "FINANCE_PAYMENT"
    TEAM_MASTER = "TEAM_MASTER"
    PROJECT_REMONT = "PROJECT_REMONT"
    ORG_FILES = "ORG_FILES"
    ACCESSION_CONTRACT_FILES = "ACCESSION_CONTRACT_FILES"
    PROVIDER_DOCS = "PROVIDER_DOCS"
    PARTNER_PROJECT_PHOTO = "PARTNER_PROJECT_PHOTO"
    PARTNER_PROJECT_PHOTO_MINI = "PARTNER_PROJECT_PHOTO_MINI"
    CONTRACTOR_LOGO = "CONTRACTOR_LOGO"
    SHOW_ROOM_PHOTO = "SHOW_ROOM_PHOTO"
    SHOW_ROOM_PHOTO_MINI = "SHOW_ROOM_PHOTO_MINI"
    MATERIAL_PHOTO = "MATERIAL_PHOTO"
    MATERIAL_PHOTO_MINI = "MATERIAL_PHOTO_MINI"
    ROOM_PHOTO = "ROOM_PHOTO"
    KITCHEN_SCHEM = "KITCHEN_SCHEM"
    PRESET_KIT_PHOTO = "PRESET_KIT_PHOTO"
    PRESET_KIT_PHOTO_MINI = "PRESET_KIT_PHOTO_MINI"
    PRESET_KIT_PRESENTATION = "PRESET_KIT_PRESENTATION"
    DDU_COMMERCIAL_OFFER = "DDU_COMMERCIAL_OFFER"
    IT_SUPPORT_FILES = "IT_SUPPORT_FILES"
    REVIT_FILES = "REVIT_FILES"


FILE_STORE_MODE_DESCRIPTIONS: dict[FileStoreMode, str] = {
    FileStoreMode.CARD_FILES: "Файлы карточки канбана",
    FileStoreMode.MASTER_FILES: "Файлы мастера",
    FileStoreMode.CHAT_FILES: "Вложения чата (оригинал)",
    FileStoreMode.CHAT_FILES_MINI: "Вложения чата (миниатюра)",
    FileStoreMode.RECIPIENT_FILES: "Файлы получателя",
    FileStoreMode.CLIENT_AGREEMENT: "Соглашение клиента",
    FileStoreMode.FLAT_LIST: "Список квартир",
    FileStoreMode.REMONT_INDICATOR: "Показатели ремонта",
    FileStoreMode.REQUEST_DOCS: "Документы заявки",
    FileStoreMode.MATERIAL_DOCS: "Документы материала",
    FileStoreMode.PLANIROVKA_PHOTOS: "Фото планировки",
    FileStoreMode.FINANCE_PAYMENT: "Файлы финансового платежа",
    FileStoreMode.TEAM_MASTER: "Файлы бригады/мастера",
    FileStoreMode.PROJECT_REMONT: "Файлы проекта ремонта",
    FileStoreMode.ORG_FILES: "Файлы организации",
    FileStoreMode.ACCESSION_CONTRACT_FILES: "Договор присоединения",
    FileStoreMode.PROVIDER_DOCS: "Документы поставщика",
    FileStoreMode.PARTNER_PROJECT_PHOTO: "Фото проекта партнёра",
    FileStoreMode.PARTNER_PROJECT_PHOTO_MINI: "Фото проекта партнёра (мини)",
    FileStoreMode.CONTRACTOR_LOGO: "Логотип подрядчика",
    FileStoreMode.SHOW_ROOM_PHOTO: "Фото шоурума",
    FileStoreMode.SHOW_ROOM_PHOTO_MINI: "Фото шоурума (мини)",
    FileStoreMode.MATERIAL_PHOTO: "Фото материала (оригинал)",
    FileStoreMode.MATERIAL_PHOTO_MINI: "Фото материала (мини)",
    FileStoreMode.ROOM_PHOTO: "Фото комнаты (design_room)",
    FileStoreMode.KITCHEN_SCHEM: "Схема кухни",
    FileStoreMode.PRESET_KIT_PHOTO: "Фото комплекта (оригинал)",
    FileStoreMode.PRESET_KIT_PHOTO_MINI: "Фото комплекта (мини)",
    FileStoreMode.PRESET_KIT_PRESENTATION: "Презентация комплекта",
    FileStoreMode.DDU_COMMERCIAL_OFFER: "Коммерческое предложение ДДУ",
    FileStoreMode.IT_SUPPORT_FILES: "Файлы IT-поддержки",
    FileStoreMode.REVIT_FILES: "Файлы Revit",
}


def _today_segment() -> str:
    return date.today().strftime("%Y.%m.%d")


def _uniq(prefix: str) -> str:
    return f"{prefix}{uuid4()}"


def build_logical_path(mode: FileStoreMode | str, ext: str, *, index: int = 1) -> str | None:
    """
    Build `/documents/...` path exactly like `KanbanController::srfileUploadAction`.
    Returns None for unknown mode.
    """
    ext = ext.lstrip(".").lower()
    day = _today_segment()
    c = index

    match str(mode):
        case FileStoreMode.CARD_FILES:
            path = f"/documents/{day}/card_files/{_uniq(f'card_file_{c}_')}.{ext}"
        case FileStoreMode.MASTER_FILES:
            path = f"/documents/{day}/master_files/{_uniq(f'master_files{c}_')}.{ext}"
        case FileStoreMode.CHAT_FILES:
            path = f"/documents/{day}/chat_files/{_uniq(f'chat_files{c}_')}.{ext}"
        case FileStoreMode.CHAT_FILES_MINI:
            path = f"/documents/{day}/chat_files/mini/{_uniq(f'chat_files{c}_')}.{ext}"
        case FileStoreMode.RECIPIENT_FILES:
            path = f"/documents/{day}/recipient_files/{_uniq(f'recipient_files{c}_')}.{ext}"
        case FileStoreMode.CLIENT_AGREEMENT:
            path = f"/documents/{day}/client_agreement/{_uniq(f'client_agreement{c}_')}.{ext}"
        case FileStoreMode.FLAT_LIST:
            path = f"/documents/{day}/flat_list/{_uniq(f'flat_list{c}_')}.{ext}"
        case FileStoreMode.REMONT_INDICATOR:
            path = f"/documents/{day}/remont_indicator/{_uniq(f'remont_indicator{c}_')}.{ext}"
        case FileStoreMode.REQUEST_DOCS:
            path = f"/documents/{day}/request_docs/{_uniq(f'request_docs{c}_')}.{ext}"
        case FileStoreMode.MATERIAL_DOCS:
            path = f"/documents/{day}/material_docs/{_uniq(f'material_docs{c}_')}.{ext}"
        case FileStoreMode.PLANIROVKA_PHOTOS:
            path = f"/documents/{day}/planirovka_photos/{_uniq(f'planirovka_photos{c}_')}.{ext}"
        case FileStoreMode.FINANCE_PAYMENT:
            path = f"/documents/{day}/finance_payment_files/{_uniq(f'finance_payment_files{c}_')}.{ext}"
        case FileStoreMode.TEAM_MASTER:
            path = f"/documents/{day}/team_master_files/{_uniq(f'team_master_files{c}_')}.{ext}"
        case FileStoreMode.PROJECT_REMONT:
            path = f"/documents/{day}/project_remont_files/{_uniq('project_remont_file_')}.{ext}"
        case FileStoreMode.ORG_FILES:
            path = f"/documents/{day}/org_files/{_uniq(f'org_files{c}_')}.{ext}"
        case FileStoreMode.ACCESSION_CONTRACT_FILES:
            path = f"/documents/{day}/accession_contract/{_uniq(f'accession_contract{c}_')}.{ext}"
        case FileStoreMode.PROVIDER_DOCS:
            path = f"/documents/{day}/provider_docs/{_uniq('doc_')}.{ext}"
        case FileStoreMode.PARTNER_PROJECT_PHOTO:
            path = f"/documents/{day}/partner_project_photo/{_uniq('photo_')}.{ext}"
        case FileStoreMode.PARTNER_PROJECT_PHOTO_MINI:
            path = f"/documents/{day}/partner_project_photo/mini/{_uniq('photo_mini_')}.{ext}"
        case FileStoreMode.CONTRACTOR_LOGO:
            path = f"/documents/contractor_logo/{_uniq('contractor_logo_')}.{ext}"
        case FileStoreMode.SHOW_ROOM_PHOTO:
            path = f"/documents/{day}/showroom_photos/{_uniq('show_room_photo_')}.{ext}"
        case FileStoreMode.SHOW_ROOM_PHOTO_MINI:
            path = f"/documents/{day}/showroom_photos/mini/{_uniq('show_room_photo_mini_')}.{ext}"
        case FileStoreMode.MATERIAL_PHOTO:
            path = f"/documents/{day}/material_photo/{_uniq('material_photo_orig_')}.{ext}"
        case FileStoreMode.MATERIAL_PHOTO_MINI:
            path = f"/documents/{day}/material_photo/mini/{_uniq('material_photo_')}.{ext}"
        case FileStoreMode.ROOM_PHOTO:
            path = f"/documents/{day}/design_room/{_uniq('room_photo_')}.{ext}"
        case FileStoreMode.KITCHEN_SCHEM:
            path = f"/documents/{day}/kitchen_schem/{_uniq('schem_')}.{ext}"
        case FileStoreMode.PRESET_KIT_PHOTO:
            path = f"/documents/{day}/preset_kit_photos/original/{_uniq('preset_kit_photo')}.{ext}"
        case FileStoreMode.PRESET_KIT_PHOTO_MINI:
            path = f"/documents/{day}/preset_kit_photos/{_uniq('preset_kit_photo')}.{ext}"
        case FileStoreMode.PRESET_KIT_PRESENTATION:
            path = f"/documents/{day}/preset_kit_presentation_files/{_uniq('preset_kit_presentation')}.{ext}"
        case FileStoreMode.DDU_COMMERCIAL_OFFER:
            path = f"/documents/{day}/ddu_commercial_offer/{_uniq(f'ddu_commercial_offer_{c}_')}.{ext}"
        case FileStoreMode.IT_SUPPORT_FILES:
            path = f"/documents/{day}/it_support_files/{_uniq(f'it_support_file_{c}_')}.{ext}"
        case FileStoreMode.REVIT_FILES:
            path = f"/documents/{day}/revit_files/{_uniq(f'revit_file_{c}_')}.{ext}"
        case _:
            return None

    return path


def logical_path_to_object_key(logical_path: str) -> str:
    """Same as `Api_MinioStorage::absolutePathToKey` for `/documents/...` paths."""
    normalized = logical_path.replace("\\", "/")
    if "/documents/" in normalized:
        pos = normalized.index("/documents/")
        return normalized[pos + 1 :]
    return normalized.lstrip("/")
