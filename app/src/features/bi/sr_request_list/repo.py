from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import BI_MODULE_CODE
from ..errors import to_bi_database_error


class SrRequestListRepository(BaseRepository):
    async def bi_client_request_list(
        self,
        iin: object | None,
        flat_guid: object | None,
        discount_percent: object | None,
    ) -> SpRows:
        try:
            return await self.call_sp(
                "rest.bi_client_request_list",
                iin,
                flat_guid,
                discount_percent if discount_percent is not None else 0,
                cursor=True,
                module_code=BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_bi_database_error(exc) from exc
