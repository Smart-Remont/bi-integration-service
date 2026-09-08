"""Stub BIG Integration / DDU Export GET services (no PostgreSQL)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from src.features.big_integration.ddu_flat_info.deps import get_ddu_flat_info_service
from src.features.big_integration.ddu_flat_info.service import DduFlatInfoService
from src.features.big_integration.ddu_request_info.deps import get_ddu_request_info_service
from src.features.big_integration.ddu_request_info.service import DduRequestInfoService
from src.features.big_integration.request_info.deps import get_request_info_service
from src.features.big_integration.request_info.service import RequestInfoService
from src.features.big_integration.request_status_info.deps import get_request_status_info_service
from src.features.big_integration.request_status_info.service import RequestStatusInfoService
from src.features.big_integration.responses import big_integration_success_response
from src.features.ddu_export.ddu_flat_list_by_resident.deps import (
    get_ddu_flat_list_by_resident_service,
)
from src.features.ddu_export.ddu_flat_list_by_resident.service import DduFlatListByResidentService
from src.features.ddu_export.ddu_flat_remont_info.deps import get_ddu_flat_remont_info_service
from src.features.ddu_export.ddu_flat_remont_info.service import DduFlatRemontInfoService
from src.features.ddu_export.ddu_resident_list.deps import get_ddu_resident_list_service
from src.features.ddu_export.ddu_resident_list.service import DduResidentListService
from src.features.ddu_export.ddu_room_list.deps import get_ddu_room_list_service
from src.features.ddu_export.ddu_room_list.service import DduRoomListService
from src.features.ddu_export.ddu_room_type_list.deps import get_ddu_room_type_list_service
from src.features.ddu_export.ddu_room_type_list.service import DduRoomTypeListService
from src.features.ddu_export.responses import ddu_export_success_response

_OVERRIDES: list[Any] = []


class _StubRequestInfoService(RequestInfoService):
    def __init__(self) -> None:
        pass

    async def request_info(
        self,
        deal_id: str,
        application_id: str,
        order_id: str,
    ) -> JSONResponse:
        return big_integration_success_response(
            {
                "deal_id": deal_id or None,
                "application_id": application_id or None,
                "order_id": order_id or None,
                "client_request_id": 1001,
            }
        )


class _StubRequestStatusInfoService(RequestStatusInfoService):
    def __init__(self) -> None:
        pass

    async def request_status_info(
        self,
        deal_id: str,
        application_id: str,
        order_id: str,
    ) -> JSONResponse:
        return big_integration_success_response(
            {
                "deal_id": deal_id or None,
                "status_code": "ACTIVE",
            }
        )


class _StubDduRequestInfoService(DduRequestInfoService):
    def __init__(self) -> None:
        pass

    async def ddu_request_info(self, client_request_id: int) -> JSONResponse:
        return big_integration_success_response(
            {
                "client_request_id": client_request_id or None,
                "order_id": "ORD-1",
            }
        )


class _StubDduFlatInfoService(DduFlatInfoService):
    def __init__(self) -> None:
        pass

    async def ddu_flat_info(self, flat_guid: str) -> JSONResponse:
        return big_integration_success_response(
            {
                "flat_guid": flat_guid or None,
                "flat_num": "101",
            }
        )


class _StubDduResidentListService(DduResidentListService):
    def __init__(self) -> None:
        pass

    async def ddu_resident_list(self) -> JSONResponse:
        return ddu_export_success_response([{"resident_guid": "guid-1", "name": "Test JK"}])


class _StubDduFlatListByResidentService(DduFlatListByResidentService):
    def __init__(self) -> None:
        pass

    async def ddu_flat_list_by_resident(self, resident_guid: str) -> JSONResponse:
        return ddu_export_success_response(
            [{"flat_guid": "flat-guid-1", "resident_guid": resident_guid or None}]
        )


class _StubDduRoomListService(DduRoomListService):
    def __init__(self) -> None:
        pass

    async def ddu_room_list(self) -> JSONResponse:
        return ddu_export_success_response([{"room_id": 1, "room_name": "Kitchen"}])


class _StubDduRoomTypeListService(DduRoomTypeListService):
    def __init__(self) -> None:
        pass

    async def ddu_room_type_list(self) -> JSONResponse:
        return ddu_export_success_response([{"room_type_id": 1, "room_type_name": "Living"}])


class _StubDduFlatRemontInfoService(DduFlatRemontInfoService):
    def __init__(self) -> None:
        pass

    async def ddu_flat_remont_info(self, flat_guid: str) -> JSONResponse:
        if not flat_guid:
            from src.features.ddu_export.responses import ddu_export_error_response

            return ddu_export_error_response(
                "Параметр flat_guid обязателен",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return ddu_export_success_response(
            {
                "client_request_id": 42,
                "remont_id": 7,
                "rooms": [
                    {
                        "room_id": 1,
                        "room_name": "Kitchen",
                        "params": [{"param_code": "AREA", "param_value": "10"}],
                    }
                ],
            }
        )


def apply_ddu_get_service_overrides(fastapi_app: FastAPI) -> None:
    pairs = [
        (get_request_info_service, lambda: _StubRequestInfoService()),
        (get_request_status_info_service, lambda: _StubRequestStatusInfoService()),
        (get_ddu_request_info_service, lambda: _StubDduRequestInfoService()),
        (get_ddu_flat_info_service, lambda: _StubDduFlatInfoService()),
        (get_ddu_resident_list_service, lambda: _StubDduResidentListService()),
        (get_ddu_flat_list_by_resident_service, lambda: _StubDduFlatListByResidentService()),
        (get_ddu_room_list_service, lambda: _StubDduRoomListService()),
        (get_ddu_room_type_list_service, lambda: _StubDduRoomTypeListService()),
        (get_ddu_flat_remont_info_service, lambda: _StubDduFlatRemontInfoService()),
    ]
    for dep, factory in pairs:
        fastapi_app.dependency_overrides[dep] = factory
        _OVERRIDES.append(dep)


def clear_service_overrides(fastapi_app: FastAPI) -> None:
    for dep in _OVERRIDES:
        fastapi_app.dependency_overrides.pop(dep, None)
    _OVERRIDES.clear()
