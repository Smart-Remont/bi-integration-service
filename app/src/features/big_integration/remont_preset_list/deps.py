from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RemontPresetListRepository
from .service import RemontPresetListService


def get_remont_preset_list_service(connection: DatabaseConnectionDep) -> RemontPresetListService:
    repository = RemontPresetListRepository(connection=connection)
    return RemontPresetListService(repository=repository)


RemontPresetListServiceDep = Annotated[RemontPresetListService, Depends(get_remont_preset_list_service)]
