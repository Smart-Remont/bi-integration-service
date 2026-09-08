from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrPresetListRepository
from .service import SrPresetListService


def get_sr_preset_list_service(connection: DatabaseConnectionDep) -> SrPresetListService:
    repository = SrPresetListRepository(connection=connection)
    return SrPresetListService(repository=repository)


SrPresetListServiceDep = Annotated[SrPresetListService, Depends(get_sr_preset_list_service)]
