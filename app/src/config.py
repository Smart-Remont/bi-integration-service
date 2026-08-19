import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class BigIntegrationAuthConfig:
    username: str = os.getenv("INTEGRATION_HS_BI_USER", "hs_bi")
    password: str = os.getenv("INTEGRATION_HS_BI_PASSWORD", "")


class InstallmentAuthConfig:
    username: str = os.getenv("INSTALLMENT_API_USER", "")
    password: str = os.getenv("INSTALLMENT_API_PASSWORD", "")


class FactoringAuthConfig:
    """Basic auth for /api/v1/factoring/*. Falls back to installment creds if unset."""

    username: str = os.getenv(
        "FACTORING_API_USER",
        os.getenv("INSTALLMENT_API_USER", ""),
    )
    password: str = os.getenv(
        "FACTORING_API_PASSWORD",
        os.getenv("INSTALLMENT_API_PASSWORD", ""),
    )


class CORSConfig:
    allow_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class MyncaConfig:
    """Client ЭЦП via existing MyNCA (same service as constructor ClientSignController)."""

    base_url: str = os.getenv("MYNCA_BASE_URL", "https://nca.smartremont.kz/api")
    token: str = os.getenv("MYNCA_TOKEN", "")
    office_public_url: str = os.getenv(
        "OFFICE_PUBLIC_URL",
        "https://office.smartremont.kz",
    )
    public_base_url: str = os.getenv(
        "PUBLIC_BASE_URL",
        "https://devintegration.smart-remont.kz",
    )


class AppConfig:
    env: str = os.getenv("APP_ENV", "stage")


cors_config = CORSConfig()
big_integration_auth_config = BigIntegrationAuthConfig()
installment_auth_config = InstallmentAuthConfig()
factoring_auth_config = FactoringAuthConfig()
mynca_config = MyncaConfig()
app_config = AppConfig()
