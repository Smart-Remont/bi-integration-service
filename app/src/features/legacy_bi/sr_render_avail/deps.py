from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrRenderAvailRepository
from .service import SrRenderAvailService


def get_sr_render_avail_service(connection: DatabaseConnectionDep) -> SrRenderAvailService:
    repository = SrRenderAvailRepository(connection=connection)
    return SrRenderAvailService(repository=repository)


SrRenderAvailServiceDep = Annotated[SrRenderAvailService, Depends(get_sr_render_avail_service)]
