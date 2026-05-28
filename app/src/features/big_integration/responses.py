from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def big_integration_success_response(data: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(data),
    )


def big_integration_error_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": message},
    )
