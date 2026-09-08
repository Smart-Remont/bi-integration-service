from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..preset.builder import PresetResponseBuilder
from ..preset.repo import PresetRenderRepository
from .service import RemontPresetService


def get_remont_preset_service(
    connection: DatabaseConnectionDep,
) -> RemontPresetService:
    repository = PresetRenderRepository(connection=connection)
    builder = PresetResponseBuilder(repository=repository)
    return RemontPresetService(repository=repository, builder=builder)


RemontPresetServiceDep = Annotated[
    RemontPresetService,
    Depends(get_remont_preset_service),
]
