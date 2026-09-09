"""Mutating parity: request-create-v3 → request-event-v3 (opt-in via PARITY_MUTATING=1).

Flow (one test, two logged steps — both must return HTTP 200 + response=true):
  1. POST create (status NEW) → client_request_id
  2. POST event (status DEAL_CREATED) with placementUUID + order_id from step 1

SP ``ddu__request_event_v3`` requires ``client_request_id``, ``placementUUID``, ``status``.
Statuses ``NEW`` / ``CLIENT_INFO`` are rejected; first real event after create is ``DEAL_CREATED``.
"""

from __future__ import annotations

import os
import uuid

import httpx
import pytest

from .parity_helpers import (
    PostParityCase,
    extract_big_integration_client_request_id,
    run_post_parity,
)

pytestmark = [pytest.mark.live, pytest.mark.parity, pytest.mark.mutating]

CREATE_CASE = PostParityCase(
    id="request-create-v3-mutating-success",
    php_action="request-create-v3",
    py_path="/api/big_integration/request-create-v3",
    body={},
)

EVENT_CASE = PostParityCase(
    id="request-event-v3-mutating-success",
    php_action="request-event-v3",
    py_path="/api/big_integration/request-event-v3",
    body={},
)

# First handled event after create (NEW). SP ignores ``event_code`` — only ``status`` matters.
DEFAULT_EVENT_STATUS = "DEAL_CREATED"


def _mutating_env() -> dict[str, str | None]:
    return {
        name: os.getenv(name)
        for name in (
            "TEST_DDU_MUTATING_FLAT_GUID",
            "TEST_DDU_MUTATING_PRESET_ID",
            "TEST_DDU_MUTATING_IIN",
            "TEST_DDU_MUTATING_ORDER_ID",
            "TEST_DDU_MUTATING_EVENT_STATUS",
            "TEST_DDU_MUTATING_FULL_NAME",
            "TEST_DDU_MUTATING_PHONE",
            "TEST_DDU_MUTATING_REQUEST_PRICE",
        )
    }


def build_mutating_create_body(env: dict[str, str | None]) -> dict[str, object] | None:
    flat_guid = (env.get("TEST_DDU_MUTATING_FLAT_GUID") or "").strip()
    preset_raw = (env.get("TEST_DDU_MUTATING_PRESET_ID") or "").strip()
    iin = (env.get("TEST_DDU_MUTATING_IIN") or "").strip()
    if not flat_guid or not preset_raw or not iin:
        return None
    if not preset_raw.isdigit():
        return None

    order_id = (env.get("TEST_DDU_MUTATING_ORDER_ID") or "").strip()
    if not order_id:
        order_id = f"PARITY-{uuid.uuid4().hex[:12]}"

    full_name = (env.get("TEST_DDU_MUTATING_FULL_NAME") or "Parity Test Client").strip()
    phone = (env.get("TEST_DDU_MUTATING_PHONE") or "+77001234567").strip()
    price_raw = (env.get("TEST_DDU_MUTATING_REQUEST_PRICE") or "").strip()

    body: dict[str, object] = {
        "application_id": None,
        "order_id": order_id,
        "deal_id": None,
        "placementUUID": flat_guid,
        "preset_id": int(preset_raw),
        "full_name": full_name,
        "phone_number": phone,
        "email": "parity-test@smartremont.kz",
        "birth_date": "01.01.1990",
        "iin": iin,
        "status": "NEW",
        "request_type": "FULL_REMONT",
        "selected_sets": [],
    }
    if price_raw:
        body["request_price"] = int(price_raw) if price_raw.isdigit() else float(price_raw)
    return body


def build_mutating_event_body(
    client_request_id: int,
    create_body: dict[str, object],
    create_data: dict[str, object],
    env: dict[str, str | None],
) -> dict[str, object]:
    """Event body aligned with ``rest.ddu__request_event_v3`` (see SP in dev_prod)."""
    flat_guid = create_body.get("placementUUID")
    if not isinstance(flat_guid, str) or not flat_guid.strip():
        raise ValueError("create_body must contain placementUUID for event step")

    status = (env.get("TEST_DDU_MUTATING_EVENT_STATUS") or DEFAULT_EVENT_STATUS).strip()
    body: dict[str, object] = {
        "client_request_id": client_request_id,
        "placementUUID": flat_guid,
        "status": status,
        "request_type": create_body.get("request_type", "FULL_REMONT"),
    }
    for key in ("order_id", "application_id", "deal_id"):
        value = create_data.get(key)
        if value is None:
            value = create_body.get(key)
        if value is not None:
            body[key] = value
    return body


@pytest.fixture
def hs_bi_live_auth(hs_bi_auth: dict[str, str], live_credentials_configured: bool) -> dict[str, str]:
    if not live_credentials_configured:
        pytest.skip("Set INTEGRATION_HS_BI_PASSWORD and DDU_EXPORT_AUTH_PASSWORD in app/.env")
    return hs_bi_auth


@pytest.fixture
def ddu_export_live_auth(
    ddu_export_auth: dict[str, str],
    live_credentials_configured: bool,
) -> dict[str, str]:
    if not live_credentials_configured:
        pytest.skip("DDU export credentials not configured")
    return ddu_export_auth


@pytest.fixture
async def parity_http_client(integrations_base_url: str) -> httpx.AsyncClient:
    timeout = httpx.Timeout(timeout=120.0, connect=15.0)
    client = httpx.AsyncClient(timeout=timeout)
    try:
        probe = await client.get(f"{integrations_base_url}/health")
        if probe.status_code != 200:
            pytest.skip(f"integrations-sr /health returned {probe.status_code}")
    except httpx.ConnectError:
        pytest.skip(f"integrations-sr not reachable at {integrations_base_url}")
    yield client
    await client.aclose()


@pytest.mark.asyncio
async def test_request_create_v3_then_event_v3_mutating_parity(
    parity_mutating_enabled: None,
    office_base_url: str,
    integrations_base_url: str,
    hs_bi_live_auth: dict[str, str],
    ddu_export_live_auth: dict[str, str],
    parity_http_client: httpx.AsyncClient,
) -> None:
    env = _mutating_env()
    create_body = build_mutating_create_body(env)
    if create_body is None:
        pytest.skip(
            "Set TEST_DDU_MUTATING_FLAT_GUID, TEST_DDU_MUTATING_PRESET_ID, "
            "TEST_DDU_MUTATING_IIN in app/.env"
        )

    php_create, py_create = await run_post_parity(
        case=CREATE_CASE,
        body=create_body,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        hs_bi_auth=hs_bi_live_auth,
        ddu_export_auth=ddu_export_live_auth,
        client=parity_http_client,
        expect_http_status=200,
    )

    php_id = extract_big_integration_client_request_id(
        php_create.parsed,
        side="OFFICE",
        case_id=CREATE_CASE.id,
    )
    py_id = extract_big_integration_client_request_id(
        py_create.parsed,
        side="FASTAPI",
        case_id=CREATE_CASE.id,
    )
    assert php_id == py_id, (
        f"[{CREATE_CASE.id}] client_request_id mismatch after create: "
        f"PHP={php_id}, FastAPI={py_id}"
    )

    create_data = php_create.parsed.get("data")
    assert isinstance(create_data, dict), f"[{CREATE_CASE.id}] missing data in OFFICE create response"
    event_body = build_mutating_event_body(php_id, create_body, create_data, env)
    await run_post_parity(
        case=EVENT_CASE,
        body=event_body,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        hs_bi_auth=hs_bi_live_auth,
        ddu_export_auth=ddu_export_live_auth,
        client=parity_http_client,
        expect_http_status=200,
    )
