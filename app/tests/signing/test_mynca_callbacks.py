"""Unit tests: MyNCA incoming callbacks (PHP ClientSign / Cabinet)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.features.signing.errors import SigningDatabaseError
from src.features.signing.services_mynca_callbacks import MyncaCallbackService, mynca_sign_page_url


@pytest.fixture
def repo() -> AsyncMock:
    mock = AsyncMock()
    mock.insert_sign_general = AsyncMock(return_value=99)
    mock.sign_tab_modify = AsyncMock()
    mock.cabinet_project_sign__set = AsyncMock()
    mock.cabinet_project_error_sign__clear = AsyncMock()
    mock.check_iin_sign_client = AsyncMock(return_value=1)
    mock.get_document_type_id_by_code = AsyncMock(return_value=10)
    mock.get_client_request_id_by_remont = AsyncMock(return_value=3200)
    mock.client_request_upd_doc = AsyncMock(return_value=50)
    mock.cabinet_document_sign_id__set = AsyncMock()
    return mock


@pytest.fixture
def service(repo: AsyncMock) -> MyncaCallbackService:
    return MyncaCallbackService(repo)


@pytest.mark.asyncio
async def test_client_sign_success_inserts(service: MyncaCallbackService, repo: AsyncMock) -> None:
    result = await service.client_sign(
        {
            "sign_process_id": "pid-1",
            "status": "SUCCESS",
            "ext_id": 100,
            "dn_name": "CN=Test",
            "group_id": "g1",
            "meta_data": {"type_code": "CLIENT_SIGN", "client_request_id": 100, "doc_type": "AGREEMENT"},
        }
    )
    assert result == {"status": True}
    repo.insert_sign_general.assert_awaited_once()
    kwargs = repo.insert_sign_general.await_args.kwargs
    assert kwargs["sign_type_code"] == "CLIENT_SIGN"
    assert kwargs["client_request_id"] == 100
    assert kwargs["sign_what"] == "MYNCA"
    repo.sign_tab_modify.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_sign_non_success_acks(service: MyncaCallbackService, repo: AsyncMock) -> None:
    result = await service.client_sign({"sign_process_id": "pid-1", "status": "EXPIRED"})
    assert result == {"status": True}
    repo.insert_sign_general.assert_not_awaited()


@pytest.mark.asyncio
async def test_client_sign_unknown_type_acks(service: MyncaCallbackService, repo: AsyncMock) -> None:
    result = await service.client_sign(
        {"sign_process_id": "pid-1", "status": "SUCCESS", "meta_data": {"type_code": "OTHER"}}
    )
    assert result == {"status": True}
    repo.insert_sign_general.assert_not_awaited()


@pytest.mark.asyncio
async def test_client_sign_requires_process_id(service: MyncaCallbackService) -> None:
    with pytest.raises(RuntimeError, match="sign_process_id"):
        await service.client_sign({"status": "SUCCESS"})


@pytest.mark.asyncio
async def test_project_remont_success(service: MyncaCallbackService, repo: AsyncMock) -> None:
    result = await service.project_remont(
        {
            "sign_process_id": "pid-2",
            "status": "SUCCESS",
            "is_signed": True,
            "ext_id": 77,
            "dn_name": "CN=X",
        }
    )
    assert result == {"status": True}
    repo.cabinet_project_sign__set.assert_awaited_once()


@pytest.mark.asyncio
async def test_project_remont_clears_on_sp_error(service: MyncaCallbackService, repo: AsyncMock) -> None:
    repo.cabinet_project_sign__set.side_effect = SigningDatabaseError("fail")
    with pytest.raises(SigningDatabaseError):
        await service.project_remont(
            {
                "sign_process_id": "pid-2",
                "status": "SUCCESS",
                "ext_id": 77,
                "dn_name": "CN=X",
            }
        )
    repo.cabinet_project_error_sign__clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_app_callback_saves_doc(service: MyncaCallbackService, repo: AsyncMock) -> None:
    result = await service.app(
        {
            "sign_process_id": "pid-3",
            "group_id": "grp",
            "status": "SUCCESS",
            "is_signed": True,
            "ext_id": 12,
            "dn_name": "CN=IIN123",
        }
    )
    assert result == {"status": True}
    repo.check_iin_sign_client.assert_awaited_once_with(12, "CN=IIN123")
    repo.client_request_upd_doc.assert_awaited_once()
    url = repo.client_request_upd_doc.await_args.kwargs["document_url"]
    assert url.endswith("pid-3")
    repo.cabinet_document_sign_id__set.assert_awaited_once()


@pytest.mark.asyncio
async def test_defect_requires_group_id(service: MyncaCallbackService) -> None:
    with pytest.raises(RuntimeError, match="sign_group_id"):
        await service.defect(
            {
                "sign_process_id": "pid-4",
                "status": "SUCCESS",
                "ext_id": 1,
            }
        )


def test_sign_page_url_slash() -> None:
    assert mynca_sign_page_url("abc").endswith("/abc")
