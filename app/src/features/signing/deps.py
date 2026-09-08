from typing import Annotated

from fastapi import Depends
from src.config import mynca_config
from src.database.deps import DatabaseConnectionDep
from src.features.factoring.ff.mynca import MyncaClient

from .repo import SigningRepository
from .services import AituFlowService, AituRedirectService, SigningCronService, SigningDownloadService, ThirdPartySignService
from .settings_repo import SigningSettingsRepository


def get_mynca_client() -> MyncaClient:
    return MyncaClient(mynca_config.base_url, mynca_config.token)


def get_signing_repo(connection: DatabaseConnectionDep) -> SigningRepository:
    return SigningRepository(connection=connection)


def get_signing_settings_repo(connection: DatabaseConnectionDep) -> SigningSettingsRepository:
    return SigningSettingsRepository(connection=connection)


def get_signing_cron_service(
    connection: DatabaseConnectionDep,
    mynca: Annotated[MyncaClient, Depends(get_mynca_client)],
) -> SigningCronService:
    return SigningCronService(
        SigningRepository(connection=connection),
        SigningSettingsRepository(connection=connection),
        mynca,
    )


def get_aitu_flow_service(
    connection: DatabaseConnectionDep,
    mynca: Annotated[MyncaClient, Depends(get_mynca_client)],
) -> AituFlowService:
    return AituFlowService(
        SigningRepository(connection=connection),
        SigningSettingsRepository(connection=connection),
        mynca,
    )


def get_aitu_redirect_service(connection: DatabaseConnectionDep) -> AituRedirectService:
    return AituRedirectService(
        SigningRepository(connection=connection),
        SigningSettingsRepository(connection=connection),
    )


def get_signing_download_service(
    connection: DatabaseConnectionDep,
    mynca: Annotated[MyncaClient, Depends(get_mynca_client)],
) -> SigningDownloadService:
    return SigningDownloadService(
        SigningRepository(connection=connection),
        mynca,
    )


def get_third_party_sign_service(connection: DatabaseConnectionDep) -> ThirdPartySignService:
    return ThirdPartySignService(SigningRepository(connection=connection))


SigningCronServiceDep = Annotated[SigningCronService, Depends(get_signing_cron_service)]
AituFlowServiceDep = Annotated[AituFlowService, Depends(get_aitu_flow_service)]
AituRedirectServiceDep = Annotated[AituRedirectService, Depends(get_aitu_redirect_service)]
SigningDownloadServiceDep = Annotated[SigningDownloadService, Depends(get_signing_download_service)]
ThirdPartySignServiceDep = Annotated[ThirdPartySignService, Depends(get_third_party_sign_service)]
SigningRepositoryDep = Annotated[SigningRepository, Depends(get_signing_repo)]
