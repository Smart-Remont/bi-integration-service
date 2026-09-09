"""Stub Payments services for HTTP unit tests (no PostgreSQL)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from src.features.payments.cloud_payments.deps import get_cloud_payments_service
from src.features.payments.cloud_payments.service import CloudPaymentsService
from src.features.payments.sberbank_callback.deps import get_sberbank_callback_service
from src.features.payments.sberbank_callback.service import SberbankCallbackService
from src.features.payments.sberbank_check_status.deps import get_sberbank_check_status_service
from src.features.payments.sberbank_check_status.service import SberbankCheckStatusService
from src.features.payments.kaspi.deps import get_kaspi_service
from src.features.payments.kaspi.service import KaspiService
from src.features.payments.kaspi.xml import check_success_xml, info_fields

_OVERRIDES: list[Any] = []

_CHECK_XML = check_success_xml(
    txn_id="HTTP-TX",
    result_code=0,
    company_bin="251240017509",
    fields=info_fields({"prop_fio": "Stub"}),
)


class _StubKaspiService(KaspiService):
    def __init__(self) -> None:
        pass

    async def handle_request_pay(
        self,
        *,
        client_ip: str,
        params: dict[str, Any],
    ) -> tuple[str, int]:
        if params.get("command") == "check":
            return _CHECK_XML, 200
        return '<?xml version="1.0"?><response><result>5</result></response>', 200

    async def handle_payment_pay(
        self,
        *,
        client_ip: str,
        params: dict[str, Any],
    ) -> tuple[str, int]:
        return await self.handle_request_pay(client_ip=client_ip, params=params)


class _StubCloudPaymentsService(CloudPaymentsService):
    def __init__(self) -> None:
        pass

    async def handle(self, mode: str, request: Request) -> JSONResponse:
        if mode == "check":
            return JSONResponse({"code": 0})
        return JSONResponse({"code": 13})


def apply_payments_service_overrides(fastapi_app: FastAPI) -> None:
    fastapi_app.dependency_overrides[get_kaspi_service] = lambda: _StubKaspiService()
    _OVERRIDES.append(get_kaspi_service)


def apply_cloud_payments_service_overrides(fastapi_app: FastAPI) -> None:
    fastapi_app.dependency_overrides[get_cloud_payments_service] = lambda: _StubCloudPaymentsService()
    _OVERRIDES.append(get_cloud_payments_service)


class _StubSberbankCallbackService(SberbankCallbackService):
    def __init__(self) -> None:
        pass

    async def handle(self, params: dict[str, Any]) -> str:
        return "0"


class _StubSberbankCheckStatusService(SberbankCheckStatusService):
    def __init__(self) -> None:
        pass

    async def poll(self) -> str:
        return "0"


def apply_sber_service_overrides(fastapi_app: FastAPI) -> None:
    fastapi_app.dependency_overrides[get_sberbank_callback_service] = lambda: _StubSberbankCallbackService()
    fastapi_app.dependency_overrides[get_sberbank_check_status_service] = lambda: _StubSberbankCheckStatusService()
    _OVERRIDES.extend([get_sberbank_callback_service, get_sberbank_check_status_service])


def clear_payments_service_overrides(fastapi_app: FastAPI) -> None:
    for dep in _OVERRIDES:
        fastapi_app.dependency_overrides.pop(dep, None)
    _OVERRIDES.clear()
