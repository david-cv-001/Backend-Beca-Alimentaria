"""Fábricas para los tests de integración.

Crean entidades en la sesión del test (que se revierte al terminar), sin
depender de datos sembrados ni de la base de desarrollo.
"""

from datetime import time

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.tenants.models import Tenant
from app.modules.users.models import User
from app.shared.types import Role

DEFAULT_PASSWORD = "admin123"
LOGIN_URL = "/api/v1/auth/login"

DEFAULT_BREAKFAST_START = time(7, 0)
DEFAULT_BREAKFAST_END = time(10, 0)
DEFAULT_LUNCH_START = time(13, 0)
DEFAULT_LUNCH_END = time(16, 0)


async def create_tenant(
    session: AsyncSession,
    *,
    folio: str = "CAF-001",
    name: str = "Cafetería Central",
    representative: str = "Laura Méndez",
    breakfast_start: time = DEFAULT_BREAKFAST_START,
    breakfast_end: time = DEFAULT_BREAKFAST_END,
    lunch_start: time = DEFAULT_LUNCH_START,
    lunch_end: time = DEFAULT_LUNCH_END,
    active: bool = True,
) -> Tenant:
    tenant = Tenant(
        folio=folio,
        name=name,
        representative=representative,
        breakfast_start=breakfast_start,
        breakfast_end=breakfast_end,
        lunch_start=lunch_start,
        lunch_end=lunch_end,
        active=active,
    )
    session.add(tenant)
    await session.flush()
    return tenant


async def create_user(
    session: AsyncSession,
    *,
    role: Role,
    username: str,
    email: str | None = None,
    tenant: Tenant | None = None,
    active: bool = True,
    password: str = DEFAULT_PASSWORD,
) -> User:
    user = User(
        tenant_id=tenant.id if tenant is not None else None,
        role=role.value,
        username=username,
        email=email or f"{username}@beca.com",
        password_hash=hash_password(password),
        full_name=f"Usuario {username}",
        phone="5551000000",
        active=active,
    )
    session.add(user)
    await session.flush()
    return user


async def login(client: AsyncClient, username: str, password: str = DEFAULT_PASSWORD) -> str:
    response = await client.post(
        LOGIN_URL, json={"usernameOrEmail": username, "password": password}
    )
    assert response.status_code == 200, response.text
    token: str = response.json()["data"]["accessToken"]
    return token
