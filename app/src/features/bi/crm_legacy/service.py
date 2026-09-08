from typing import Any

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import bi_error_response, bi_success_response
from .repo import CrmLegacyRepository


class CrmLegacyService(BaseService):
    def __init__(self, repository: CrmLegacyRepository) -> None:
        self.repository = repository

    async def crm_create_client_request_empty(self, body: dict[str, Any]) -> JSONResponse:
        flat_guid = body.get("flat_guid")
        if not flat_guid:
            return bi_error_response("flat_guid is required")
        try:
            value = await self.repository.bi_create_client_request(str(flat_guid))
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
        return bi_success_response(value)

    async def crm_create_client_request_agreement(self, body: dict[str, Any]) -> JSONResponse:
        try:
            value = await self.repository.bi_create_client_request_agreement(body)
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
        return bi_success_response(value)

    async def create_request(self, body: dict[str, Any]) -> JSONResponse:
        try:
            client_request_id = await self.repository.bi_create_request(body)
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
        if not client_request_id:
            return bi_error_response("create request failed")
        try:
            material_json = await self.repository.bi_get_client_request_material_json(client_request_id)
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
        return bi_success_response(parse_scalar_json(material_json))

    async def sr_remont_report(self) -> JSONResponse:
        try:
            value = await self.repository.sr_remont_report()
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
        return bi_success_response(parse_scalar_json(value))
