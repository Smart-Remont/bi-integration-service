from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrShowroomReportRepository
from .service import SrShowroomReportService


def get_sr_showroom_report_service(connection: DatabaseConnectionDep) -> SrShowroomReportService:
    repository = SrShowroomReportRepository(connection=connection)
    return SrShowroomReportService(repository=repository)


SrShowroomReportServiceDep = Annotated[SrShowroomReportService, Depends(get_sr_showroom_report_service)]
