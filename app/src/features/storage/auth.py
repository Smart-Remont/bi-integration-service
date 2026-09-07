from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from src.config import storage_auth_config

security = HTTPBasic()


def verify_storage_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> None:
    if not (storage_auth_config.username and storage_auth_config.password):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage API credentials are not configured.",
        )
    username_ok = compare_digest(
        credentials.username.encode(),
        storage_auth_config.username.encode(),
    )
    password_ok = compare_digest(
        credentials.password.encode(),
        storage_auth_config.password.encode(),
    )
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


StorageBasicAuthDep = Annotated[None, Depends(verify_storage_basic_auth)]
