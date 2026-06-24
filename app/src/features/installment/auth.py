from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from src.config import installment_auth_config

security = HTTPBasic()


def verify_installment_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> None:
    username_ok = compare_digest(
        credentials.username.encode(),
        installment_auth_config.username.encode(),
    )
    password_ok = compare_digest(
        credentials.password.encode(),
        installment_auth_config.password.encode(),
    )
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


InstallmentBasicAuthDep = Annotated[
    None,
    Depends(verify_installment_basic_auth),
]
