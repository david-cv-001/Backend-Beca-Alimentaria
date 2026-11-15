from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.models import User
from app.shared.types import Role

LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"


async def _create_superadmin(session: AsyncSession) -> User:
    user = User(
        tenant_id=None,
        role=Role.SUPERADMIN.value,
        username="superadmin",
        email="superadmin@beca.com",
        password_hash=hash_password("admin123"),
        full_name="Super Administrador",
        phone="0000000000",
        active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def test_login_returns_token_and_user(client: AsyncClient, session: AsyncSession) -> None:
    await _create_superadmin(session)

    response = await client.post(
        LOGIN_URL, json={"usernameOrEmail": "superadmin", "password": "admin123"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["accessToken"]
    assert data["user"]["username"] == "superadmin"
    assert data["user"]["fullName"] == "Super Administrador"
    assert data["user"]["roles"] == ["Superadmin"]
    assert data["user"]["tenantId"] is None
    assert data["user"]["tenantName"] is None


async def test_login_accepts_email_case_insensitive(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_superadmin(session)

    response = await client.post(
        LOGIN_URL, json={"usernameOrEmail": "SUPERADMIN@BECA.COM", "password": "admin123"}
    )

    assert response.status_code == 200


async def test_login_wrong_password_is_401(client: AsyncClient, session: AsyncSession) -> None:
    await _create_superadmin(session)

    response = await client.post(
        LOGIN_URL, json={"usernameOrEmail": "superadmin", "password": "incorrecta"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "process": "AUTH_LOGIN",
        "message": "Usuario o contraseña incorrectos",
        "errors": [],
    }


async def test_login_inactive_user_is_401(client: AsyncClient, session: AsyncSession) -> None:
    user = await _create_superadmin(session)
    user.active = False
    await session.flush()

    response = await client.post(
        LOGIN_URL, json={"usernameOrEmail": "superadmin", "password": "admin123"}
    )

    assert response.status_code == 401
    assert response.json()["message"] == "La cuenta está desactivada"


async def test_login_missing_fields_is_400(client: AsyncClient) -> None:
    response = await client.post(LOGIN_URL, json={})

    assert response.status_code == 400
    body = response.json()
    assert body["process"] == "AUTH_LOGIN"
    assert body["message"] == "Datos inválidos"
    assert len(body["errors"]) == 2


async def test_me_requires_token(client: AsyncClient) -> None:
    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["process"] == "AUTH_ME"


async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.get(ME_URL, headers={"Authorization": "Bearer no.es.un.token"})

    assert response.status_code == 401
    assert response.json()["process"] == "AUTH_ME"


async def test_me_returns_authenticated_user(client: AsyncClient, session: AsyncSession) -> None:
    await _create_superadmin(session)
    login = await client.post(
        LOGIN_URL, json={"usernameOrEmail": "superadmin", "password": "admin123"}
    )
    token = login.json()["data"]["accessToken"]

    response = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["data"]["username"] == "superadmin"
    assert response.json()["data"]["roles"] == ["Superadmin"]
