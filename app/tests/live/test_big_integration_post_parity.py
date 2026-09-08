"""100% parity: legacy PHP vs integrations-sr for big_integration POST (read-only)."""

from __future__ import annotations

import os

import httpx
import pytest

from .parity_helpers import PostParityCase, assert_post_parity, resolve_body

pytestmark = [pytest.mark.live, pytest.mark.parity]

BIG_INTEGRATION_POST_CASES: tuple[PostParityCase, ...] = (
    PostParityCase(
        id="repair-pack-prices",
        php_action="repair-pack-prices",
        py_path="/api/big_integration/repair-pack-prices",
        body={"placementUUIDs": [""]},
        list_env=(("placementUUIDs", "TEST_DDU_FLAT_GUID"),),
    ),
    PostParityCase(
        id="request-constructives",
        php_action="request-constructives",
        py_path="/api/big_integration/request-constructives",
        body={"client_request_id": 0},
        required_env=(("client_request_id", "TEST_DDU_CLIENT_REQUEST_ID"),),
    ),
    PostParityCase(
        id="remont-preset-list-v2",
        php_action="remont-preset-list-v2",
        py_path="/api/big_integration/remont-preset-list-v2",
        body={"placementUUID": ""},
        required_env=(("placementUUID", "TEST_DDU_FLAT_GUID_WITH_PRESETS"),),
        require_non_empty=("data", "preset_list"),
    ),
    PostParityCase(
        id="remont-preset",
        php_action="remont-preset",
        py_path="/api/big_integration/remont-preset",
        body={"placementUUID": "", "preset_id": 0},
        required_env=(
            ("placementUUID", "TEST_DDU_FLAT_GUID_WITH_PRESETS"),
            ("preset_id", "TEST_DDU_PRESET_ID"),
        ),
        require_non_empty=("data", "preset_list"),
    ),
    PostParityCase(
        id="request-create-v3-empty",
        php_action="request-create-v3",
        py_path="/api/big_integration/request-create-v3",
        body={},
    ),
    PostParityCase(
        id="request-event-v3-empty",
        php_action="request-event-v3",
        py_path="/api/big_integration/request-event-v3",
        body={},
    ),
    PostParityCase(
        id="request-event-v3-not-found",
        php_action="request-event-v3",
        py_path="/api/big_integration/request-event-v3",
        body={"client_request_id": 999999999},
    ),
    PostParityCase(
        id="ddu-flat-info-multiple",
        php_action="ddu-flat-info-multiple",
        py_path="/api/big_integration/ddu-flat-info-multiple",
        body={"flat_guids": [""]},
        list_env=(("flat_guids", "TEST_DDU_FLAT_GUID"),),
    ),
    PostParityCase(
        id="ddu-flat-info-multiple-empty",
        php_action="ddu-flat-info-multiple",
        py_path="/api/big_integration/ddu-flat-info-multiple",
        body={"flat_guids": []},
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
    return {
        name: os.getenv(name)
        for name in (
            "TEST_DDU_FLAT_GUID",
            "TEST_DDU_FLAT_GUID_WITH_PRESETS",
            "TEST_DDU_CLIENT_REQUEST_ID",
            "TEST_DDU_PRESET_ID",
        )
    }


@pytest.mark.parametrize("case", BIG_INTEGRATION_POST_CASES, ids=lambda c: c.id)
@pytest.mark.asyncio
async def test_big_integration_post_parity(
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
