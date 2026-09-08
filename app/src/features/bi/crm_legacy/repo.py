import json
from typing import Any

from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import BI_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import to_bi_database_error


class CrmLegacyRepository(BaseRepository):
    async def bi_create_client_request(self, flat_guid: str) -> object | None:
        try:
            rows = await self.call_sp(
                "rest.bi_create_client_request",
                flat_guid,
                module_code=BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_bi_database_error(exc) from exc
        return scalar_from_sp_rows(rows)

    async def bi_create_client_request_agreement(self, body: dict[str, Any]) -> object | None:
        try:
            rows: SpRows = await self.call_sp(
                "rest.bi_create_client_request_agreement",
                body.get("application_id"),
                body.get("fio"),
                body.get("iin"),
                body.get("agreement_num"),
                body.get("preset_code"),
                body.get("status"),
                body.get("flat_guid"),
                body.get("agreement_date"),
                body.get("discount_percent"),
                cursor=True,
                module_code=BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_bi_database_error(exc) from exc
        if not rows:
            return None
        return next(iter(rows[0].values()))

    async def bi_create_request(self, body: dict[str, Any]) -> object | None:
        try:
            rows: SpRows = await self.call_sp(
                "rest.bi_create_request",
                body.get("application_id"),
                body.get("fio"),
                body.get("iin"),
                body.get("doc_date"),
                body.get("doc_num"),
                body.get("doc_issued"),
                body.get("phone_number"),
                body.get("email"),
                body.get("address"),
                body.get("preset_code"),
                body.get("flat_guid"),
                body.get("flat_num"),
                body.get("agreement_date"),
                body.get("agreement_num"),
                cursor=True,
                module_code=BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_bi_database_error(exc) from exc
        if not rows:
            return None
        return next(iter(rows[0].values()))

    async def bi_get_client_request_material_json(self, client_request_id: object) -> object | None:
        try:
            rows = await self.call_sp(
                "rest.bi_get_client_request_material_json",
                client_request_id,
                module_code=BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_bi_database_error(exc) from exc
        return scalar_from_sp_rows(rows)

    async def sr_remont_report(self) -> object | None:
        try:
            rows = await self.call_sp(
                "rest.sr_remont_report",
                module_code=BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_bi_database_error(exc) from exc
        return scalar_from_sp_rows(rows)
