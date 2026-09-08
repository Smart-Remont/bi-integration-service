"""Unit tests: GET /api/big_integration/* (mocked DB)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_info_requires_auth(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/big_integration/request-info")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_request_info_success(
    api_client: AsyncClient,
    hs_bi_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/big_integration/request-info",
        params={"deal_id": "D-1", "application_id": "A-2", "order_id": "O-3"},
        headers=hs_bi_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert_envelope(body)
    assert body["data"]["deal_id"] == "D-1"
    assert body["data"]["client_request_id"] == 1001


@pytest.mark.asyncio
async def test_request_status_info_success(
    api_client: AsyncClient,
    hs_bi_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/big_integration/request-status-info",
        params={"deal_id": "D-99"},
        headers=hs_bi_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert_envelope(body)
    assert body["data"]["status_code"] == "ACTIVE"


@pytest.mark.asyncio
async def test_ddu_request_info_zero_means_null(
    api_client: AsyncClient,
    hs_bi_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/big_integration/ddu-request-info",
        params={"client_request_id": 0},
        headers=hs_bi_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert_envelope(body)
    assert body["data"]["client_request_id"] is None


@pytest.mark.asyncio
async def test_ddu_flat_info(
    api_client: AsyncClient,
    hs_bi_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/big_integration/ddu-flat-info",
        params={"flat_guid": "11111111-2222-3333-4444-555555555555"},
        headers=hs_bi_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert_envelope(body)
    assert body["data"]["flat_num"] == "101"
