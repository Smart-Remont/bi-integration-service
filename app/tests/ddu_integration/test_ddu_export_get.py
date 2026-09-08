"""Unit tests: GET /api/ddu_export/* (mocked DB)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ddu_resident_list_requires_auth(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/ddu_export/ddu-resident-list")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ddu_resident_list_success(
    api_client: AsyncClient,
    ddu_export_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/ddu_export/ddu-resident-list",
        headers=ddu_export_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert_envelope(body)
    assert isinstance(body["data"], list)
    assert body["data"][0]["name"] == "Test JK"


@pytest.mark.asyncio
async def test_ddu_room_list_and_room_type_list(
    api_client: AsyncClient,
    ddu_export_auth: dict[str, str],
    assert_envelope,
) -> None:
    for path in ("/api/ddu_export/ddu-room-list", "/api/ddu_export/ddu-room-type-list"):
        response = await api_client.get(path, headers=ddu_export_auth)
        assert response.status_code == 200
        assert_envelope(response.json())


@pytest.mark.asyncio
async def test_ddu_flat_list_by_resident(
    api_client: AsyncClient,
    ddu_export_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/ddu_export/ddu-flat-list-by-resident",
        params={"resident_guid": "resident-guid-1"},
        headers=ddu_export_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert_envelope(body)
    assert body["data"][0]["resident_guid"] == "resident-guid-1"


@pytest.mark.asyncio
async def test_ddu_flat_remont_info_requires_flat_guid(
    api_client: AsyncClient,
    ddu_export_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/ddu_export/ddu-flat-remont-info",
        headers=ddu_export_auth,
    )
    assert response.status_code == 400
    assert_envelope(response.json(), expect_success=False)


@pytest.mark.asyncio
async def test_ddu_flat_remont_info_nested_rooms(
    api_client: AsyncClient,
    ddu_export_auth: dict[str, str],
    assert_envelope,
) -> None:
    response = await api_client.get(
        "/api/ddu_export/ddu-flat-remont-info",
        params={"flat_guid": "11111111-2222-3333-4444-555555555555"},
        headers=ddu_export_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert_envelope(body)
    assert body["data"]["rooms"][0]["params"][0]["param_code"] == "AREA"
