import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class BigIntegrationAuthConfig:
    username: str = os.getenv("INTEGRATION_HS_BI_USER", "hs_bi")
    password: str = os.getenv("INTEGRATION_HS_BI_PASSWORD", "")


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
app_config = AppConfig()
