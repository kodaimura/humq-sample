from typing import Any, Optional
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


class NoContentResponse(Response):
    def __init__(self, response: Optional[Response] = None):
        headers = dict(response.headers) if response else {}
        super().__init__(status_code=204, headers=headers)


class ApiResponse:
    @staticmethod
    def _build_response(
        data: Any,
        status_code: int,
        response: Optional[Response] = None,
    ) -> JSONResponse:
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        encoded = jsonable_encoder(data)
        headers = dict(response.headers) if response else {}

        return JSONResponse(
            content=encoded,
            status_code=status_code,
            headers=headers,
        )

    # ----------------------------------------
    # 200 OK
    # ----------------------------------------
    @classmethod
    def ok(
        cls,
        data: Any = None,
        response: Optional[Response] = None,
        status_code: int = 200,
    ) -> JSONResponse:
        return cls._build_response(
            data=data,
            status_code=status_code,
            response=response,
        )

    # ----------------------------------------
    # 201 Created
    # ----------------------------------------
    @classmethod
    def created(
        cls,
        data: Any = None,
        response: Optional[Response] = None,
    ) -> JSONResponse:
        return cls._build_response(
            data=data,
            status_code=201,
            response=response,
        )

    # ----------------------------------------
    # 204 No Content
    # ----------------------------------------
    @classmethod
    def no_content(
        cls,
        response: Optional[Response] = None,
    ) -> NoContentResponse:
        return NoContentResponse(response=response)

    # ----------------------------------------
    # 400 Bad Request
    # ----------------------------------------
    @classmethod
    def error(
        cls,
        data: Any = None,
        status_code: int = 400,
    ) -> JSONResponse:
        return cls._build_response(
            data=data,
            status_code=status_code,
        )

    # ----------------------------------------
    # 401 Unauthorized
    # ----------------------------------------
    @classmethod
    def unauthorized(cls, message: str = "Unauthorized") -> JSONResponse:
        return cls._build_response(
            data={"detail": message},
            status_code=401,
        )

    # ----------------------------------------
    # 404 Not Found
    # ----------------------------------------
    @classmethod
    def not_found(cls, message: str = "Resource not found") -> JSONResponse:
        return cls._build_response(
            data={"detail": message},
            status_code=404,
        )
