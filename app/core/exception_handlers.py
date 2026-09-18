import logging
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle application and routing HTTP errors consistently.
    """

    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "status": "error",
            "message": (
                exc.detail
                if isinstance(exc.detail, str)
                else "Request failed"
            ),
            "data": None,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic/FastAPI request validation errors.
    """

    errors = jsonable_encoder(exc.errors())

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation failed",
            "data": {
                "errors": errors,
            },
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected server errors without exposing
    internal implementation details.
    """
    logging.exception(
        "Unhandled exception | method=%s | path=%s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "data": None,
        },
    )
