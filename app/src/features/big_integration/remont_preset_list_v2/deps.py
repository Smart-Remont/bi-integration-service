from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..preset.builder import PresetResponseBuilder
from ..preset.repo import PresetRenderRepository
from .service import RemontPresetListV2Service


def get_remont_preset_list_v2_service(
    connection: DatabaseConnectionDep,
) -> RemontPresetListV2Service:
    repository = PresetRenderRepository(connection=connection)
    builder = PresetResponseBuilder(repository=repository)
    return RemontPresetListV2Service(repository=repository, builder=builder)


RemontPresetListV2ServiceDep = Annotated[
    RemontPresetListV2Service,
    Depends(get_remont_preset_list_v2_service),
]
