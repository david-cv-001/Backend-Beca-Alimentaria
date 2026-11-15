from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Excepción base compartida.

    Los servicios lanzan excepciones de dominio; el handler las traduce al
    envelope ``{ process, message, errors }`` que consume el frontend.

    Si ``process`` no se fija explícitamente, el handler usa el nombre de la
    ruta en curso (``TENANT_CREATE``, ``USER_UPDATE``...), que es el código de
    operación que el frontend espera. Así los servicios no repiten códigos.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    process: str | None = None
    default_message: str = "Ocurrió un error inesperado"

    def __init__(
        self,
        message: str | None = None,
        errors: list[str] | None = None,
        process: str | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.errors = errors or []
        if process is not None:
            self.process = process
        super().__init__(self.message)


class BadRequestException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Solicitud inválida"


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Credenciales inválidas"


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "No tiene permisos para esta operación"


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Recurso no encontrado"


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Ya existe un registro con ese valor"


def error_payload(process: str, message: str, errors: list[str] | None = None) -> dict[str, Any]:
    return {"process": process, "message": message, "errors": errors or []}


def route_process(request: Request) -> str:
    """Código ``process`` del endpoint en curso (nombre de la ruta).

    Los routers declaran ``name="TENANT_CREATE"`` etc. para que los errores de
    validación y de autorización hereden el código de la operación.
    """
    route = request.scope.get("route")
    return getattr(route, "name", None) or "API_ERROR"


def _format_validation_error(error: dict[str, Any]) -> str:
    parts = [str(part) for part in error["loc"] if part not in {"body", "query", "path", "header"}]
    field = ".".join(parts) if parts else "body"
    return f"{field}: {error['msg']}"


def register_exception_handlers(app: FastAPI) -> None:
    """Un solo handler para las excepciones de dominio, más dos adaptadores de framework."""

    @app.exception_handler(AppException)
    async def _handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.process or route_process(request), exc.message, exc.errors),
        )

    # FastAPI responde 422 por defecto; se unifica a 400 con nuestro envelope.
    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_payload(
                route_process(request),
                "Datos inválidos",
                [_format_validation_error(error) for error in exc.errors()],
            ),
        )

    # HTTPException de FastAPI/Starlette (401, 403, 404 de rutas) también usa el envelope.
    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(route_process(request), str(exc.detail)),
        )
