from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import time

from app.core.config import config
from app.core.response import ApiResponse
from app.core.logger import logger
from app.core.error import AppError
from .router import api_router


is_prod = config.APP_ENV == "production"

app = FastAPI(
    title="humq-sample2",
    version="1.0.0",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api")


# =================================
# Middleware
# =================================


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    duration_ms = int((time.time() - start) * 1000)
    account_id = getattr(request.state, "account_id", None)
    account = {"id": account_id} if account_id is not None else None

    if request.method != "OPTIONS":
        logger.info(
            "access",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client": request.client.host if request.client else None,
                "account": account,
            },
        )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin"

    if is_prod:
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    return response


# =================================
# Exception Handlers
# =================================


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    account_id = getattr(request.state, "account_id", None)

    logger.warning(
        "application error occurred",
        extra={
            "error_type": "app_error",
            "error_code": exc.code,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "account_id": account_id,
        },
    )
    return ApiResponse.error(
        data={"code": exc.code, "details": exc.details},
        status_code=exc.status_code,
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    account_id = getattr(request.state, "account_id", None)

    logger.warning(
        "http exception occurred",
        extra={
            "error_type": "http_exception",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url),
            "method": request.method,
            "account_id": account_id,
        },
    )
    return ApiResponse.error(
        data={"message": exc.detail or "HTTP error"},
        status_code=exc.status_code,
    )


@app.exception_handler(SQLAlchemyError)
async def handle_db_error(request: Request, exc: SQLAlchemyError):
    account_id = getattr(request.state, "account_id", None)

    logger.exception(
        "database error occurred",
        extra={
            "error_type": "database_error",
            "path": str(request.url),
            "method": request.method,
            "account_id": account_id,
        },
    )
    return ApiResponse.error(
        data={"message": "Database error occurred"},
        status_code=500,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    account_id = getattr(request.state, "account_id", None)

    logger.warning(
        "validation error occurred",
        extra={
            "error_type": "validation_error",
            "status_code": 422,
            "errors": exc.errors(),
            "path": str(request.url),
            "method": request.method,
            "account_id": account_id,
        },
    )
    return ApiResponse.error(
        data={"message": "Validation error", "errors": exc.errors()},
        status_code=422,
    )


@app.exception_handler(Exception)
async def handle_generic_error(request: Request, exc: Exception):
    account_id = getattr(request.state, "account_id", None)

    logger.exception(
        "unexpected error occurred",
        extra={
            "error_type": "unexpected_error",
            "error_class": type(exc).__name__,
            "path": str(request.url),
            "method": request.method,
            "account_id": account_id,
        },
    )
    return ApiResponse.error(
        data={"message": "Internal server error"},
        status_code=500,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
