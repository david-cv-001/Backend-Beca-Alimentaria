from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.types import Role
from tests.factories import create_tenant, create_user, login

TENANTS_URL = "/api/v1/tenants"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _tenant_payload(**overrides: object) -> dict[str, object]:
    """Payload de cafetería con horarios válidos; cada test sobreescribe lo que necesita."""
    payload: dict[str, object] = {
        "folio": "CAF-001",
        "name": "Cafetería Central",
        "representative": "Ana Torres",
        "breakfastStart": "07:00",
        "breakfastEnd": "10:00",
        "lunchStart": "13:00",
        "lunchEnd": "16:00",
        "active": True,
    }
    payload.update(overrides)
    return payload


async def _superadmin_token(client: AsyncClient, session: AsyncSession) -> str:
    await create_user(session, role=Role.SUPERADMIN, username="superadmin")
    return await login(client, "superadmin")


async def test_list_tenants_returns_paginated_envelope(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    await create_tenant(session, folio="CAF-002", name="Cafetería Beta")
    await create_tenant(session, folio="CAF-001", name="Cafetería Alfa")

    response = await client.get(TENANTS_URL, headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert [tenant["name"] for tenant in body["data"]] == ["Cafetería Alfa", "Cafetería Beta"]
    assert body["pagination"] == {
        "page": 1,
        "pageSize": 10,
        "sortBy": "name",
        "sortDirection": "ASC",
        "totalElements": 2,
        "totalPages": 1,
    }


async def test_list_tenants_paginates(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)
    for index in range(3):
        await create_tenant(session, folio=f"CAF-00{index}", name=f"Cafetería {index}")

    response = await client.get(
        TENANTS_URL, headers=_auth(token), params={"page": 2, "pageSize": 2}
    )

    body = response.json()
    assert len(body["data"]) == 1
    assert body["pagination"]["page"] == 2
    assert body["pagination"]["totalElements"] == 3
    assert body["pagination"]["totalPages"] == 2


async def test_list_tenants_invalid_sort_field_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.get(
        TENANTS_URL, headers=_auth(token), params={"sortBy": "password:asc"}
    )

    assert response.status_code == 400
    assert response.json()["process"] == "TENANT_LIST"


async def test_list_tenants_sorts_by_representative(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    await create_tenant(session, folio="CAF-002", name="Cafetería Beta", representative="Zoe Ramos")
    await create_tenant(
        session, folio="CAF-001", name="Cafetería Alfa", representative="Ana Torres"
    )

    response = await client.get(
        TENANTS_URL, headers=_auth(token), params={"sortBy": "representative:asc"}
    )

    assert response.status_code == 200
    representatives = [tenant["representative"] for tenant in response.json()["data"]]
    assert representatives == ["Ana Torres", "Zoe Ramos"]


async def test_get_tenant(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")

    response = await client.get(f"{TENANTS_URL}/{tenant.id}", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["data"]["folio"] == "CAF-001"
    assert response.json()["data"]["breakfastStart"] == "07:00"
    assert response.json()["data"]["lunchEnd"] == "16:00"


async def test_get_tenant_not_found(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)

    response = await client.get(
        f"{TENANTS_URL}/00000000-0000-0000-0000-000000000000", headers=_auth(token)
    )

    assert response.status_code == 404
    assert response.json()["process"] == "TENANT_GET"


async def test_create_tenant_normalizes_folio(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(folio="caf-009", name="Cafetería Nueva"),
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["folio"] == "CAF-009"
    assert data["active"] is True
    assert data["createdAt"].endswith("Z")


async def test_create_tenant_duplicate_folio_is_409(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    await create_tenant(session, folio="CAF-001", name="Cafetería Central")

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(folio="caf-001", name="Otra Cafetería"),
    )

    assert response.status_code == 409
    assert response.json()["process"] == "TENANT_CREATE"
    assert response.json()["message"] == "Ya existe una cafetería con ese folio"


async def test_create_tenant_duplicate_name_case_insensitive_is_409(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    await create_tenant(session, folio="CAF-001", name="Cafetería Central")

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(folio="CAF-002", name="cafetería central"),
    )

    assert response.status_code == 409
    assert response.json()["message"] == "Ya existe una cafetería con ese nombre"


async def test_create_tenant_invalid_folio_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(folio="ab", name="Cafetería Mala"),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["process"] == "TENANT_CREATE"
    assert body["message"] == "Datos inválidos"
    assert "folio: Debe tener al menos 3 caracteres" in body["errors"]


async def test_create_tenant_rejects_symbols_in_name(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(folio="CAF-010", name="Cafe <script>"),
    )

    assert response.status_code == 400
    assert response.json()["process"] == "TENANT_CREATE"


async def test_create_tenant_stores_meal_schedule(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(
            breakfastStart="07:30",
            breakfastEnd="10:30",
            lunchStart="14:00",
            lunchEnd="17:00",
        ),
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["breakfastStart"] == "07:30"
    assert data["breakfastEnd"] == "10:30"
    assert data["lunchStart"] == "14:00"
    assert data["lunchEnd"] == "17:00"


async def test_create_tenant_accepts_seconds_in_meal_time(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(breakfastStart="07:00:00", breakfastEnd="10:00:00"),
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["breakfastStart"] == "07:00"
    assert data["breakfastEnd"] == "10:00"


async def test_create_tenant_requires_meal_schedule(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json={"folio": "CAF-001", "name": "Cafetería Central", "representative": "Ana Torres"},
    )

    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "breakfastStart: Este campo es obligatorio" in errors
    assert "breakfastEnd: Este campo es obligatorio" in errors
    assert "lunchStart: Este campo es obligatorio" in errors
    assert "lunchEnd: Este campo es obligatorio" in errors


async def test_create_tenant_invalid_meal_time_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(breakfastStart="25:00"),
    )

    assert response.status_code == 400
    assert "breakfastStart: No es una hora válida" in response.json()["errors"]


async def test_create_tenant_end_before_start_is_400(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)

    response = await client.post(
        TENANTS_URL,
        headers=_auth(token),
        json=_tenant_payload(breakfastEnd="06:00"),
    )

    assert response.status_code == 400
    assert (
        "breakfastEnd: La hora de fin debe ser posterior a la hora de inicio"
        in response.json()["errors"]
    )


async def test_update_tenant(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")

    response = await client.put(
        f"{TENANTS_URL}/{tenant.id}",
        headers=_auth(token),
        json=_tenant_payload(name="Cafetería Renombrada"),
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Cafetería Renombrada"


async def test_update_tenant_conflict_is_409(client: AsyncClient, session: AsyncSession) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")
    await create_tenant(session, folio="CAF-002", name="Cafetería Sur")

    response = await client.put(
        f"{TENANTS_URL}/{tenant.id}",
        headers=_auth(token),
        json=_tenant_payload(name="Cafetería Sur"),
    )

    assert response.status_code == 409
    assert response.json()["process"] == "TENANT_UPDATE"


async def test_update_tenant_keeping_own_values_is_ok(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")

    response = await client.put(
        f"{TENANTS_URL}/{tenant.id}",
        headers=_auth(token),
        json=_tenant_payload(representative="Otra Persona"),
    )

    assert response.status_code == 200


async def test_update_tenant_changes_meal_schedule(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")

    response = await client.put(
        f"{TENANTS_URL}/{tenant.id}",
        headers=_auth(token),
        json=_tenant_payload(lunchStart="12:30", lunchEnd="15:30"),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["lunchStart"] == "12:30"
    assert data["lunchEnd"] == "15:30"


async def test_change_status_deactivates_tenant_users(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")
    checker = await create_user(session, role=Role.CHECKER, username="checker1", tenant=tenant)

    response = await client.patch(
        f"{TENANTS_URL}/{tenant.id}/status", headers=_auth(token), json={"active": False}
    )

    assert response.status_code == 200
    assert response.json()["data"]["active"] is False
    await session.refresh(checker)
    assert checker.active is False


async def test_reactivating_tenant_does_not_reactivate_users(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = await _superadmin_token(client, session)
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central", active=False)
    checker = await create_user(
        session, role=Role.CHECKER, username="checker1", tenant=tenant, active=False
    )

    response = await client.patch(
        f"{TENANTS_URL}/{tenant.id}/status", headers=_auth(token), json={"active": True}
    )

    assert response.status_code == 200
    assert response.json()["data"]["active"] is True
    await session.refresh(checker)
    assert checker.active is False


async def test_tenants_require_superadmin(client: AsyncClient, session: AsyncSession) -> None:
    tenant = await create_tenant(session, folio="CAF-001", name="Cafetería Central")
    await create_user(session, role=Role.ADMIN, username="admin1", tenant=tenant)
    token = await login(client, "admin1")

    response = await client.get(TENANTS_URL, headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["process"] == "TENANT_LIST"


async def test_tenants_require_token(client: AsyncClient) -> None:
    response = await client.get(TENANTS_URL)

    assert response.status_code == 401
    assert response.json()["process"] == "TENANT_LIST"
