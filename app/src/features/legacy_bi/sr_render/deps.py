from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrRenderRepository
from .service import SrRenderService


def get_sr_render_service(connection: DatabaseConnectionDep) -> SrRenderService:
    repository = SrRenderRepository(connection=connection)
    return SrRenderService(repository=repository)


SrRenderServiceDep = Annotated[SrRenderService, Depends(get_sr_render_service)]
