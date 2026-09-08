from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrResidentReportRepository
from .service import SrResidentReportService


def get_sr_resident_report_service(connection: DatabaseConnectionDep) -> SrResidentReportService:
    repository = SrResidentReportRepository(connection=connection)
    return SrResidentReportService(repository=repository)


SrResidentReportServiceDep = Annotated[SrResidentReportService, Depends(get_sr_resident_report_service)]
