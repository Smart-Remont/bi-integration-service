"""100% parity: legacy PHP (devprod) vs integrations-sr for hs_bi POST (read-only)."""

from __future__ import annotations

import os

import httpx
import pytest

from .parity_helpers import PostParityCase, assert_post_parity, resolve_body

pytestmark = [pytest.mark.live, pytest.mark.parity]

BI_POST_CASES: tuple[PostParityCase, ...] = (
    PostParityCase(
        id="sr-showroom-report",
        php_action="sr-showroom-report",
        py_path="/api/integration/sr-showroom-report",
        body={},
    ),
    PostParityCase(
        id="sr-resident-report",
        php_action="sr-resident-report",
        py_path="/api/integration/sr-resident-report",
        body={},
    ),
    PostParityCase(
        id="sr-preset-list",
        php_action="sr-preset-list",
        py_path="/api/integration/sr-preset-list",
        body={},
        py_extra_headers={
            "Host": "devprod.smart-remont.kz",
            "X-Forwarded-Proto": "https",
        },
    ),
    PostParityCase(
        id="sr-render",
        php_action="sr-render",
        py_path="/api/integration/sr-render",
        body={"flat_guid": ""},
        required_env=(("flat_guid", "TEST_DDU_FLAT_GUID"),),
    ),
    PostParityCase(
        id="sr-request-list",
        php_action="sr-request-list",
        py_path="/api/integration/sr-request-list",
        body={"flat_guid": ""},
        required_env=(("flat_guid", "TEST_DDU_FLAT_GUID"),),
    ),
    PostParityCase(
        id="remont-avail",
        php_action="remont-avail",
        py_path="/api/integration/remont-avail",
        body={"flat_guid": ""},
        required_env=(("flat_guid", "TEST_DDU_FLAT_GUID"),),
    ),
    PostParityCase(
        id="get-constructives",
        php_action="get-constructives",
        py_path="/api/integration/get-constructives",
        body={"application_id": ""},
        required_env=(("application_id", "TEST_DDU_APPLICATION_ID"),),
    ),
    PostParityCase(
        id="sr-render-avail",
        php_action="sr-render-avail",
        py_path="/api/integration/sr-render-avail",
        body={"flat_guid": [""]},
        list_env=(("flat_guid", "TEST_DDU_FLAT_GUID"),),
    ),
    PostParityCase(
        id="sr-remont-avail",
        php_action="sr-remont-avail",
        py_path="/api/integration/sr-remont-avail",
        body={"realEstateUUIDs": [""]},
        list_env=(("realEstateUUIDs", "TEST_REAL_ESTATE_GUID"),),
    ),
    PostParityCase(
        id="sr-stage",
        php_action="sr-stage",
        py_path="/api/integration/sr-stage",
        body=[{"iin": "", "id": ""}],
        required_env=(
            ("iin", "TEST_CLIENT_IIN"),
            ("id", "TEST_DDU_FLAT_GUID"),
        ),
    ),
    PostParityCase(
        id="change-request-status-invalid",
        php_action="change-request-status",
        py_path="/api/integration/change-request-status",
        body={"application_id": 0, "status_code": "INVALID"},
    ),
    PostParityCase(
        id="bigapp-form-empty",
        php_action="bigapp-form",
        py_path="/api/integration/bigapp-form",
        body={},
    ),
    PostParityCase(
        id="big-crm-form-empty",
        php_action="big-crm-form",
        py_path="/api/integration/big-crm-form",
        body={},
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


def _env_snapshot() -> dict[str, str | None]:
    names = [
        "TEST_DDU_FLAT_GUID",
        "TEST_DDU_RESIDENT_GUID",
        "TEST_DDU_APPLICATION_ID",
        "TEST_REAL_ESTATE_GUID",
        "TEST_CLIENT_IIN",
    ]
    return {name: os.getenv(name) for name in names}


@pytest.mark.parametrize("case", BI_POST_CASES, ids=lambda c: c.id)
@pytest.mark.asyncio
async def test_bi_post_parity(
    case: PostParityCase,
    office_base_url: str,
    integrations_base_url: str,
    hs_bi_live_auth: dict[str, str],
    ddu_export_live_auth: dict[str, str],
    parity_http_client: httpx.AsyncClient,
) -> None:
    body = resolve_body(case, env=_env_snapshot())
    if body is None:
        missing = [e for _, e in case.required_env] or [e for _, e in case.list_env]
        pytest.skip(f"Set env for case {case.id}: {missing}")

    await assert_post_parity(
        case=case,
        body=body,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        hs_bi_auth=hs_bi_live_auth,
        ddu_export_auth=ddu_export_live_auth,
        client=parity_http_client,
    )
