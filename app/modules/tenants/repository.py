from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestException
from app.modules.tenants.models import Tenant
from app.modules.users.models import User


class TenantRepository:
    """Acceso a datos de cafeterías."""

    # Lista blanca de ordenamiento: evita inyección en el ORDER BY.
    SORTABLE: dict[str, Any] = {
        "folio": Tenant.folio,
        "name": Tenant.name,
        "representative": Tenant.representative,
        "active": Tenant.active,
        "createdAt": Tenant.created_at,
        "created_at": Tenant.created_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _ordered(self, sort_field: str, sort_direction: str) -> Select[Any]:
        column = self.SORTABLE.get(sort_field)
        if column is None:
            raise BadRequestException(f"Campo de ordenamiento no permitido: {sort_field}")
        return select(Tenant).order_by(column.asc() if sort_direction == "ASC" else column.desc())

    async def find_all(
        self, *, offset: int, limit: int, sort_field: str, sort_direction: str
    ) -> list[Tenant]:
        result = await self.session.scalars(
            self._ordered(sort_field, sort_direction).offset(offset).limit(limit)
        )
        return list(result)

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(Tenant)) or 0

    async def find_by_id(self, tenant_id: UUID) -> Tenant | None:
        return await self.session.get(Tenant, tenant_id)

    async def find_by_folio(self, folio: str, *, exclude_id: UUID | None = None) -> Tenant | None:
        stmt = select(Tenant).where(func.lower(Tenant.folio) == folio.lower())
        if exclude_id is not None:
            stmt = stmt.where(Tenant.id != exclude_id)
        return await self.session.scalar(stmt)

    async def find_by_name(self, name: str, *, exclude_id: UUID | None = None) -> Tenant | None:
        stmt = select(Tenant).where(func.lower(Tenant.name) == name.lower())
        if exclude_id is not None:
            stmt = stmt.where(Tenant.id != exclude_id)
        return await self.session.scalar(stmt)

    async def add(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def deactivate_users(self, tenant_id: UUID) -> None:
        """Cascada de desactivación: apaga a todos los usuarios activos del tenant."""
        await self.session.execute(
            update(User)
            .where(User.tenant_id == tenant_id, User.active.is_(True))
            .values(active=False)
        )
