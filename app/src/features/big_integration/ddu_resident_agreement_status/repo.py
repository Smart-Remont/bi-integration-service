import json

from src.repository import BaseRepository

from ..errors import to_big_integration_database_error

_DDU_MODULE_CODE = "DDU"


class DduResidentAgreementStatusRepository(BaseRepository):
    async def ddu_resident_agreement_log_insert(
        self,
        payload: dict[str, object],
    ) -> None:
        try:
            await self.call_sp(
                "rest.ddu_resident_agreement__log_insert",
                json.dumps(payload),
                module_code=_DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc
