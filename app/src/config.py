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


class AppConfig:
    env: str = os.getenv("APP_ENV", "stage")


cors_config = CORSConfig()
big_integration_auth_config = BigIntegrationAuthConfig()
installment_auth_config = InstallmentAuthConfig()
factoring_auth_config = FactoringAuthConfig()
app_config = AppConfig()
