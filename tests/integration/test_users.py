from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.modules.tenants.models import Tenant
from app.shared.types import Role
from tests.factories import create_tenant, create_user, login

USERS_URL = "/api/v1/users"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _superadmin_token(client: AsyncClient, session: AsyncSession) -> str:
    await create_user(session, role=Role.SUPERADMIN, username="superadmin")
    return await login(client, "superadmin")


async def _admin_token(client: AsyncClient, session: AsyncSession) -> tuple[str, Tenant]:
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")
    await create_user(session, role=Role.ADMIN, username="admin1", tenant=tenant)
    return await login(client, "admin1"), tenant


def _payload(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "username": "checker1",
        "password": "claveSegura123",
        "role": "Checker",
        "fullName": "Carlos Ruiz",
        "phone": "5551000003",
        "email": "carlos.ruiz@beca.com",
        "active": True,
    }
    data.update(overrides)
    return data


# --- Listado ---------------------------------------------------------------


async def test_list_users_returns_paginated_envelope(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    await create_user(session, role=Role.CHECKER, username="zulu", tenant=tenant)
    await create_user(session, role=Role.ADMIN, username="alfa", tenant=tenant)

    response = await client.get(USERS_URL, headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert [user["username"] for user in body["data"]] == ["alfa", "superadmin", "zulu"]
    assert body["pagination"]["sortBy"] == "username"
    assert body["pagination"]["sortDirection"] == "ASC"
    assert body["pagination"]["totalElements"] == 3


async def test_list_users_admin_sees_only_own_tenant(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, tenant = await _admin_token(client, session)
    other = await create_tenant(session, folio="CAF-002", name="Cafetería Sur")
    await create_user(session, role=Role.CHECKER, username="mine", tenant=tenant)
    await create_user(session, role=Role.CHECKER, username="foreign", tenant=other)

    response = await client.get(USERS_URL, headers=_auth(token))

    assert response.status_code == 200
    usernames = {user["username"] for user in response.json()["data"]}
    assert usernames == {"admin1", "mine"}
    assert response.json()["pagination"]["totalElements"] == 2


async def test_list_users_invalid_sort_field_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.get(
        USERS_URL, headers=_auth(token), params={"sortBy": "passwordHash:asc"}
    )

    assert response.status_code == 400
    assert response.json()["process"] == "USER_LIST"


async def test_list_users_forbidden_for_checker(client: AsyncClient, session: AsyncSession) -> None:
    tenant = await create_tenant(session)
    await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)
    token = await login(client, "checker1")

    response = await client.get(USERS_URL, headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["process"] == "USER_LIST"


async def test_list_users_requires_token(client: AsyncClient) -> None:
    response = await client.get(USERS_URL)

    assert response.status_code == 401
    assert response.json()["process"] == "USER_LIST"


# --- Consulta --------------------------------------------------------------


async def test_get_user_includes_denormalized_tenant_name(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")
    user = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.get(f"{USERS_URL}/{user.id}", headers=_auth(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["role"] == "Checker"
    assert data["tenantName"] == "Cafetería Central"


async def test_get_user_from_other_tenant_is_404(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, _ = await _admin_token(client, session)
    other = await create_tenant(session, folio="CAF-002", name="Cafetería Sur")
    foreign = await create_user(session, role=Role.CHECKER, username="foreign", tenant=other)

    response = await client.get(f"{USERS_URL}/{foreign.id}", headers=_auth(token))

    assert response.status_code == 404
    assert response.json()["process"] == "USER_GET"


async def test_get_user_not_found(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)

    response = await client.get(
        f"{USERS_URL}/00000000-0000-0000-0000-000000000000", headers=_auth(token)
    )

    assert response.status_code == 404


# --- Alta ------------------------------------------------------------------


async def test_superadmin_creates_admin(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)

    response = await client.post(
        USERS_URL, headers=_auth(token), json=_payload(role="Admin", tenantId=str(tenant.id))
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["role"] == "Admin"
    assert data["tenantId"] == str(tenant.id)
    assert data["tenantName"] == "Cafetería Central"
    assert "passwordHash" not in data
    assert "password_hash" not in data


async def test_superadmin_creating_admin_without_tenant_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(USERS_URL, headers=_auth(token), json=_payload(role="Admin"))

    assert response.status_code == 400
    assert response.json()["process"] == "USER_CREATE"
    assert response.json()["message"] == "Debe indicar la cafetería del usuario"


async def test_superadmin_cannot_create_superadmin(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(USERS_URL, headers=_auth(token), json=_payload(role="Superadmin"))

    assert response.status_code == 403
    assert response.json()["process"] == "USER_CREATE"


async def test_admin_creates_checker_and_forces_own_tenant(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, tenant = await _admin_token(client, session)
    other = await create_tenant(session, folio="CAF-002", name="Cafetería Sur")

    response = await client.post(
        USERS_URL, headers=_auth(token), json=_payload(role="Checker", tenantId=str(other.id))
    )

    assert response.status_code == 201
    assert response.json()["data"]["tenantId"] == str(tenant.id)


async def test_admin_cannot_create_admin(client: AsyncClient, session: AsyncSession) -> None:
    token, tenant = await _admin_token(client, session)

    response = await client.post(
        USERS_URL, headers=_auth(token), json=_payload(role="Admin", tenantId=str(tenant.id))
    )

    assert response.status_code == 403
    assert response.json()["process"] == "USER_CREATE"


async def test_admin_cannot_create_superadmin(client: AsyncClient, session: AsyncSession) -> None:
    token, _ = await _admin_token(client, session)

    response = await client.post(USERS_URL, headers=_auth(token), json=_payload(role="Superadmin"))

    assert response.status_code == 403


async def test_create_user_duplicate_username_is_409(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.post(
        USERS_URL, headers=_auth(token), json=_payload(tenantId=str(tenant.id))
    )

    assert response.status_code == 409
    assert response.json()["message"] == "Ya existe un usuario con ese nombre de usuario"


async def test_create_user_duplicate_email_case_insensitive_is_409(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    await create_user(
        session, role=Role.CHECKER, username="checker1", email="carlos@beca.com", tenant=tenant
    )

    response = await client.post(
        USERS_URL,
        headers=_auth(token),
        json=_payload(username="checker2", email="CARLOS@BECA.COM", tenantId=str(tenant.id)),
    )

    assert response.status_code == 409
    assert response.json()["message"] == "Ya existe un usuario con ese correo"


async def test_create_user_normalizes_username_and_email(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)

    response = await client.post(
        USERS_URL,
        headers=_auth(token),
        json=_payload(
            username="Checker.Uno", email="Carlos.Ruiz@Beca.com", tenantId=str(tenant.id)
        ),
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["username"] == "checker.uno"
    assert data["email"] == "carlos.ruiz@beca.com"


async def test_create_user_invalid_username_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)

    response = await client.post(
        USERS_URL, headers=_auth(token), json=_payload(username="ab", tenantId=str(tenant.id))
    )

    assert response.status_code == 400
    body = response.json()
    assert body["process"] == "USER_CREATE"
    assert any("username" in error for error in body["errors"])


async def test_create_user_invalid_email_is_400(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)

    response = await client.post(
        USERS_URL,
        headers=_auth(token),
        json=_payload(email="no-es-correo", tenantId=str(tenant.id)),
    )

    assert response.status_code == 400
    assert any("email" in error for error in response.json()["errors"])


async def test_create_user_short_password_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)

    response = await client.post(
        USERS_URL,
        headers=_auth(token),
        json=_payload(password="corta", tenantId=str(tenant.id)),
    )

    assert response.status_code == 400
    assert any("password" in error for error in response.json()["errors"])


async def test_create_user_unknown_tenant_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        USERS_URL,
        headers=_auth(token),
        json=_payload(tenantId="00000000-0000-0000-0000-000000000000"),
    )

    assert response.status_code == 400
    assert response.json()["message"] == "La cafetería indicada no existe"


# --- Actualización ---------------------------------------------------------


async def test_update_user_without_password_keeps_hash(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    user = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)
    original_hash = user.password_hash

    response = await client.put(
        f"{USERS_URL}/{user.id}",
        headers=_auth(token),
        json={
            "fullName": "Carlos Ruiz Actualizado",
            "role": "Checker",
            "tenantId": str(tenant.id),
            "phone": "5551000003",
            "email": "carlos.ruiz@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["fullName"] == "Carlos Ruiz Actualizado"
    await session.refresh(user)
    assert user.password_hash == original_hash


async def test_update_user_with_password_rehashes(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    user = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.put(
        f"{USERS_URL}/{user.id}",
        headers=_auth(token),
        json={
            "fullName": "Carlos Ruiz",
            "role": "Checker",
            "tenantId": str(tenant.id),
            "phone": "5551000003",
            "email": "carlos.ruiz@beca.com",
            "active": True,
            "password": "nuevaClave123",
        },
    )

    assert response.status_code == 200
    await session.refresh(user)
    assert verify_password("nuevaClave123", user.password_hash)


async def test_admin_updates_checker_of_own_tenant(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, tenant = await _admin_token(client, session)
    checker = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.put(
        f"{USERS_URL}/{checker.id}",
        headers=_auth(token),
        json={
            "fullName": "Checker Renombrado",
            "role": "Checker",
            "phone": "5551000003",
            "email": "checker1@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["fullName"] == "Checker Renombrado"


async def test_admin_updates_user_of_other_tenant_is_404(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, _ = await _admin_token(client, session)
    other = await create_tenant(session, folio="CAF-002", name="Cafetería Sur")
    foreign = await create_user(session, role=Role.CHECKER, username="foreign", tenant=other)

    response = await client.put(
        f"{USERS_URL}/{foreign.id}",
        headers=_auth(token),
        json={
            "fullName": "Intruso",
            "role": "Checker",
            "phone": "5551000003",
            "email": "foreign@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["process"] == "USER_UPDATE"


async def test_admin_cannot_assign_admin_role_is_403(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, tenant = await _admin_token(client, session)
    checker = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.put(
        f"{USERS_URL}/{checker.id}",
        headers=_auth(token),
        json={
            "fullName": "Checker Ascendido",
            "role": "Admin",
            "phone": "5551000003",
            "email": "checker1@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 403


async def test_admin_cannot_edit_another_admin_is_403(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, tenant = await _admin_token(client, session)
    peer = await create_user(session, role=Role.ADMIN, username="admin2", tenant=tenant)

    response = await client.put(
        f"{USERS_URL}/{peer.id}",
        headers=_auth(token),
        json={
            "fullName": "Otro Admin",
            "role": "Admin",
            "phone": "5551000004",
            "email": "admin2@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["process"] == "USER_UPDATE"


async def test_superadmin_cannot_assign_superadmin_role_is_403(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    checker = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.put(
        f"{USERS_URL}/{checker.id}",
        headers=_auth(token),
        json={
            "fullName": "Checker",
            "role": "Superadmin",
            "phone": "5551000003",
            "email": "checker1@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 403


async def test_superadmin_can_update_own_profile_keeping_role(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    me = await client.get("/api/v1/auth/me", headers=_auth(token))
    user_id = me.json()["data"]["id"]

    response = await client.put(
        f"{USERS_URL}/{user_id}",
        headers=_auth(token),
        json={
            "fullName": "Super Admin Editado",
            "role": "Superadmin",
            "phone": "5551000000",
            "email": "superadmin@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["role"] == "Superadmin"
    assert data["fullName"] == "Super Admin Editado"


async def test_update_user_duplicate_email_is_409(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    first = await create_user(
        session, role=Role.CHECKER, username="checker1", email="uno@beca.com", tenant=tenant
    )
    await create_user(
        session, role=Role.CHECKER, username="checker2", email="dos@beca.com", tenant=tenant
    )

    response = await client.put(
        f"{USERS_URL}/{first.id}",
        headers=_auth(token),
        json={
            "fullName": "Carlos Ruiz",
            "role": "Checker",
            "tenantId": str(tenant.id),
            "phone": "5551000003",
            "email": "DOS@beca.com",
            "active": True,
        },
    )

    assert response.status_code == 409
    assert response.json()["process"] == "USER_UPDATE"


# --- Estado ----------------------------------------------------------------


async def test_superadmin_changes_status(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session)
    checker = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.patch(
        f"{USERS_URL}/{checker.id}/status", headers=_auth(token), json={"active": False}
    )

    assert response.status_code == 200
    assert response.json()["data"]["active"] is False
    await session.refresh(checker)
    assert checker.active is False


async def test_admin_changes_status_of_own_checker(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, tenant = await _admin_token(client, session)
    checker = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.patch(
        f"{USERS_URL}/{checker.id}/status", headers=_auth(token), json={"active": False}
    )

    assert response.status_code == 200


async def test_admin_status_on_other_tenant_is_404(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, _ = await _admin_token(client, session)
    other = await create_tenant(session, folio="CAF-002", name="Cafetería Sur")
    foreign = await create_user(session, role=Role.CHECKER, username="foreign", tenant=other)

    response = await client.patch(
        f"{USERS_URL}/{foreign.id}/status", headers=_auth(token), json={"active": False}
    )

    assert response.status_code == 404
    assert response.json()["process"] == "USER_STATUS"


async def test_admin_cannot_change_status_of_another_admin(
    client: AsyncClient, session: AsyncSession
) -> None:
    token, tenant = await _admin_token(client, session)
    peer = await create_user(session, role=Role.ADMIN, username="admin2", tenant=tenant)

    response = await client.patch(
        f"{USERS_URL}/{peer.id}/status", headers=_auth(token), json={"active": False}
    )

    assert response.status_code == 403
