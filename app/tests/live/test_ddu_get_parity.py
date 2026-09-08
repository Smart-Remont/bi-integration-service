"""100% parity: legacy PHP (devprod) vs integrations-sr for DDU GET endpoints.

Both services must use the **same PostgreSQL** (same SP data) or bodies will differ.

Required in app/.env:
  INTEGRATION_HS_BI_PASSWORD, DDU_EXPORT_AUTH_PASSWORD

Optional (skip case if missing):
  TEST_DDU_DEAL_ID, TEST_DDU_APPLICATION_ID, TEST_DDU_ORDER_ID
  TEST_DDU_CLIENT_REQUEST_ID, TEST_DDU_FLAT_GUID, TEST_DDU_RESIDENT_GUID

Run:
  uv run pytest app/tests/live/test_ddu_get_parity.py -m parity -v

integrations-sr must be up at INTEGRATIONS_BASE_URL (default http://127.0.0.1:8000).
Office: OFFICE_BASE_URL (default https://devprod.smart-remont.kz).
"""

from __future__ import annotations

import os

import httpx
import pytest

from .parity_helpers import GetParityCase, assert_get_parity, resolve_params

pytestmark = [pytest.mark.live, pytest.mark.parity]

BIG_INTEGRATION_CASES: tuple[GetParityCase, ...] = (
    GetParityCase(
        id="request-info",
        php_action="request-info",
        py_path="/api/big_integration/request-info",
        params={"deal_id": "", "application_id": "", "order_id": ""},
        auth="hs_bi",
        any_required_env=(
            ("deal_id", "TEST_DDU_DEAL_ID"),
            ("application_id", "TEST_DDU_APPLICATION_ID"),
            ("order_id", "TEST_DDU_ORDER_ID"),
        ),
    ),
    GetParityCase(
        id="request-status-info",
        php_action="request-status-info",
        py_path="/api/big_integration/request-status-info",
        params={"deal_id": "", "application_id": "", "order_id": ""},
        auth="hs_bi",
        any_required_env=(
            ("deal_id", "TEST_DDU_DEAL_ID"),
            ("application_id", "TEST_DDU_APPLICATION_ID"),
            ("order_id", "TEST_DDU_ORDER_ID"),
        ),
    ),
    GetParityCase(
        id="ddu-request-info",
        php_action="ddu-request-info",
        py_path="/api/big_integration/ddu-request-info",
        params={"client_request_id": 0},
        auth="hs_bi",
        required_env=(("client_request_id", "TEST_DDU_CLIENT_REQUEST_ID"),),
    ),
    GetParityCase(
        id="ddu-flat-info",
        php_action="ddu-flat-info",
        py_path="/api/big_integration/ddu-flat-info",
        params={"flat_guid": ""},
        auth="hs_bi",
        required_env=(("flat_guid", "TEST_DDU_FLAT_GUID"),),
    ),
)

DDU_EXPORT_CASES: tuple[GetParityCase, ...] = (
    GetParityCase(
        id="ddu-resident-list",
        php_action="ddu-resident-list",
        py_path="/api/ddu_export/ddu-resident-list",
        params={},
        auth="ddu_export",
    ),
    GetParityCase(
        id="ddu-room-list",
        php_action="ddu-room-list",
        py_path="/api/ddu_export/ddu-room-list",
        params={},
        auth="ddu_export",
    ),
    GetParityCase(
        id="ddu-room-type-list",
        php_action="ddu-room-type-list",
        py_path="/api/ddu_export/ddu-room-type-list",
        params={},
        auth="ddu_export",
    ),
    GetParityCase(
        id="ddu-flat-list-by-resident",
        php_action="ddu-flat-list-by-resident",
        py_path="/api/ddu_export/ddu-flat-list-by-resident",
        params={"resident_guid": ""},
        auth="ddu_export",
        required_env=(("resident_guid", "TEST_DDU_RESIDENT_GUID"),),
    ),
    GetParityCase(
        id="ddu-flat-remont-info",
        php_action="ddu-flat-remont-info",
        py_path="/api/ddu_export/ddu-flat-remont-info",
        params={"flat_guid": ""},
        auth="ddu_export",
        required_env=(("flat_guid", "TEST_DDU_FLAT_GUID"),),
    ),
    GetParityCase(
        id="ddu-flat-remont-info-missing-guid",
        php_action="ddu-flat-remont-info",
        py_path="/api/ddu_export/ddu-flat-remont-info",
        params={},
        auth="ddu_export",
    ),
)


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
    timeout = httpx.Timeout(timeout=60.0, connect=15.0)
    client = httpx.AsyncClient(timeout=timeout)
    try:
        probe = await client.get(f"{integrations_base_url}/health")
        if probe.status_code != 200:
            pytest.skip(f"integrations-sr /health returned {probe.status_code}")
    except httpx.ConnectError:
        pytest.skip(f"integrations-sr not reachable at {integrations_base_url}")
    yield client
    await client.aclose()


def _env_snapshot() -> dict[str, str | None]:
    names = [
        "TEST_DDU_DEAL_ID",
        "TEST_DDU_APPLICATION_ID",
        "TEST_DDU_ORDER_ID",
        "TEST_DDU_CLIENT_REQUEST_ID",
        "TEST_DDU_FLAT_GUID",
        "TEST_DDU_RESIDENT_GUID",
    ]
    return {name: os.getenv(name) for name in names}


@pytest.mark.parametrize("case", BIG_INTEGRATION_CASES, ids=lambda c: c.id)
@pytest.mark.asyncio
async def test_big_integration_get_parity(
    case: GetParityCase,
    office_base_url: str,
    integrations_base_url: str,
    hs_bi_live_auth: dict[str, str],
    ddu_export_live_auth: dict[str, str],
    parity_http_client: httpx.AsyncClient,
) -> None:
    params = resolve_params(case, env=_env_snapshot())
    if params is None:
        missing = [e for _, e in case.required_env] or [e for _, e in case.any_required_env]
        pytest.skip(f"Set env for case {case.id}: {missing}")

    await assert_get_parity(
        case=case,
        params=params,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        hs_bi_auth=hs_bi_live_auth,
        ddu_export_auth=ddu_export_live_auth,
        client=parity_http_client,
    )


@pytest.mark.parametrize("case", DDU_EXPORT_CASES, ids=lambda c: c.id)
@pytest.mark.asyncio
async def test_ddu_export_get_parity(
    case: GetParityCase,
    office_base_url: str,
    integrations_base_url: str,
    hs_bi_live_auth: dict[str, str],
    ddu_export_live_auth: dict[str, str],
    parity_http_client: httpx.AsyncClient,
) -> None:
    params = resolve_params(case, env=_env_snapshot())
    if params is None:
        missing = [e for _, e in case.required_env] or [e for _, e in case.any_required_env]
        pytest.skip(f"Set env for case {case.id}: {missing}")

    await assert_get_parity(
        case=case,
        params=params,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        hs_bi_auth=hs_bi_live_auth,
        ddu_export_auth=ddu_export_live_auth,
        client=parity_http_client,
    )
