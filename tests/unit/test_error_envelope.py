from collections.abc import Iterator

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient

from app.core.errors import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
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
