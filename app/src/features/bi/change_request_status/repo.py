from src.repository import BaseRepository

from ..constants import BI_MODULE_CODE
from ..errors import to_bi_database_error


class ChangeRequestStatusRepository(BaseRepository):
    async def bi_change_request_status(
        self,
        client_request_id: object | None,
        status_code: object | None,
    ) -> object | None:
        try:
            rows = await self.call_sp(
                "rest.bi_change_request_status",
                client_request_id,
                status_code,
                cursor=True,
                module_code=BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_bi_database_error(exc) from exc

        if not rows:
            return None
        return next(iter(rows[0].values()))
