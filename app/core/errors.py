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


# Mensajes de validación orientados al usuario final. La clave es el ``type``
# que emite Pydantic; lo que no aparezca aquí se deja tal cual (mensaje técnico,
# en inglés) porque no está pensado para mostrarse.
VALIDATION_MESSAGES: dict[str, str] = {
    "missing": "Este campo es obligatorio",
    "string_type": "Debe ser texto",
    "string_too_short": "Debe tener al menos {min_length} caracteres",
    "string_too_long": "No puede superar los {max_length} caracteres",
    "string_pattern_mismatch": "El formato no es válido",
    "int_parsing": "Debe ser un número entero",
    "int_type": "Debe ser un número entero",
    "greater_than_equal": "Debe ser mayor o igual a {ge}",
    "less_than_equal": "Debe ser menor o igual a {le}",
    "bool_parsing": "Debe ser verdadero o falso",
    "bool_type": "Debe ser verdadero o falso",
    "uuid_parsing": "No es un identificador válido",
    "enum": "No es un valor permitido",
    "datetime_parsing": "No es una fecha válida",
}

_EMAIL_REASON_MESSAGE = "El correo no es válido"


def _translate_validation_error(error: dict[str, Any]) -> str:
    """Traduce al español el motivo de un error de validación de Pydantic.

    Los mensajes sin traducción conocida se devuelven tal cual (inglés): son
    técnicos y no se muestran al usuario.
    """
    error_type = error.get("type", "")
    context = error.get("ctx") or {}

    if error_type == "value_error":
        # Nuestros validadores adjuntan el ``ValueError`` original, ya en español.
        custom = context.get("error")
        if custom is not None:
            return str(custom)
        # ``EmailStr`` adjunta ``reason`` en inglés; se unifica al español.
        if "reason" in context:
            return _EMAIL_REASON_MESSAGE
        return "Valor inválido"

    template = VALIDATION_MESSAGES.get(error_type)
    if template is None:
        return str(error.get("msg", "Valor inválido"))
    try:
        return template.format(**context)
    except (KeyError, IndexError):
        return template


def _format_validation_error(error: dict[str, Any]) -> str:
    parts = [str(part) for part in error["loc"] if part not in {"body", "query", "path", "header"}]
    field = ".".join(parts) if parts else "body"
    return f"{field}: {_translate_validation_error(error)}"


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
