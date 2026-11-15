from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient

from app.core.errors import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    _format_validation_error,
    register_exception_handlers,
)

EXCEPTION_CASES = [
    (UnauthorizedException, 401),
    (ForbiddenException, 403),
    (NotFoundException, 404),
    (ConflictException, 409),
]


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/domain-error")
    async def domain_error(kind: str) -> None:
        for exc_class, _ in EXCEPTION_CASES:
            if exc_class.__name__ == kind:
                raise exc_class("mensaje de prueba", process="TENANT_CREATE")
        raise AppException("inesperado")

    @app.get("/validated")
    async def validated(page: int = Query(ge=1)) -> dict[str, int]:
        return {"page": page}

    return app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(_build_app()) as test_client:
        yield test_client


@pytest.mark.parametrize(("exc_class", "status_code"), EXCEPTION_CASES)
def test_domain_exceptions_use_envelope(
    client: TestClient, exc_class: type[AppException], status_code: int
) -> None:
    response = client.get("/domain-error", params={"kind": exc_class.__name__})

    assert response.status_code == status_code
    assert response.json() == {
        "process": "TENANT_CREATE",
        "message": "mensaje de prueba",
        "errors": [],
    }


def test_validation_error_is_400_with_envelope(client: TestClient) -> None:
    response = client.get("/validated", params={"page": 0})

    assert response.status_code == 400
    body = response.json()
    assert body["process"] == "validated"
    assert body["message"] == "Datos inválidos"
    assert body["errors"] and body["errors"][0].startswith("page:")


def test_unknown_route_uses_envelope(client: TestClient) -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert set(response.json()) == {"process", "message", "errors"}


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            {"type": "missing", "loc": ("email",), "msg": "Field required"},
            "email: Este campo es obligatorio",
        ),
        (
            {
                "type": "string_too_short",
                "loc": ("username",),
                "msg": "String should have at least 3 characters",
                "ctx": {"min_length": 3},
            },
            "username: Debe tener al menos 3 caracteres",
        ),
        (
            {
                "type": "string_too_long",
                "loc": ("phone",),
                "msg": "String should have at most 15 characters",
                "ctx": {"max_length": 15},
            },
            "phone: No puede superar los 15 caracteres",
        ),
        (
            {
                "type": "string_pattern_mismatch",
                "loc": ("folio",),
                "msg": "String should match pattern '^[A-Z0-9-]+$'",
                "ctx": {"pattern": "^[A-Z0-9-]+$"},
            },
            "folio: El formato no es válido",
        ),
        (
            {
                "type": "value_error",
                "loc": ("email",),
                "msg": "value is not a valid email address: An email address must have an @-sign.",
                "ctx": {"reason": "An email address must have an @-sign."},
            },
            "email: El correo no es válido",
        ),
        (
            {
                "type": "value_error",
                "loc": ("role",),
                "msg": "Value error, El rol no es válido",
                "ctx": {"error": ValueError("El rol no es válido")},
            },
            "role: El rol no es válido",
        ),
        (
            # Sin traducción conocida: se conserva el mensaje técnico (inglés).
            {"type": "untranslated_type", "loc": ("x",), "msg": "technical english"},
            "x: technical english",
        ),
    ],
)
def test_validation_messages_are_translated(error: dict[str, Any], expected: str) -> None:
    assert _format_validation_error(error) == expected
