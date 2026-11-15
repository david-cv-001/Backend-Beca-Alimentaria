from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.core.errors import BadRequestException
from app.modules.tenants.models import Tenant
from app.modules.users.models import User


class UserRepository:
    """Acceso a datos de usuarios."""

    # Lista blanca de ordenamiento: evita inyección en el ORDER BY.
    SORTABLE: dict[str, Any] = {
        "username": User.username,
        "fullName": User.full_name,
        "full_name": User.full_name,
        "role": User.role,
        "phone": User.phone,
        "email": User.email,
        "tenantName": Tenant.name,
        "tenant_name": Tenant.name,
        "active": User.active,
        "createdAt": User.created_at,
        "created_at": User.created_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base(self, tenant_id: UUID | None) -> Select[Any]:
        """Consulta base; ``tenant_id`` no nulo aplica el aislamiento multi-tenant.

        El join con ``tenants`` es explícito (``contains_eager``) para poder
        ordenar por ``tenantName``; si se dejara al eager load, SQLAlchemy
        crearía un alias y el ``ORDER BY`` apuntaría a una tabla ausente del
        ``FROM``. ``isouter=True`` conserva al superadmin (sin cafetería).
        """
        stmt = select(User).join(User.tenant, isouter=True).options(contains_eager(User.tenant))
        if tenant_id is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)
        return stmt

    def _ordered(self, stmt: Select[Any], sort_field: str, sort_direction: str) -> Select[Any]:
        column = self.SORTABLE.get(sort_field)
        if column is None:
            raise BadRequestException(f"Campo de ordenamiento no permitido: {sort_field}")
        return stmt.order_by(column.asc() if sort_direction == "ASC" else column.desc())

    async def find_all(
        self,
        *,
        tenant_id: UUID | None,
        offset: int,
        limit: int,
        sort_field: str,
        sort_direction: str,
    ) -> list[User]:
        stmt = self._ordered(self._base(tenant_id), sort_field, sort_direction)
        result = await self.session.scalars(stmt.offset(offset).limit(limit))
        return list(result)

    async def count(self, *, tenant_id: UUID | None) -> int:
        stmt = select(func.count()).select_from(User)
        if tenant_id is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)
        return await self.session.scalar(stmt) or 0

    async def find_by_id(self, user_id: UUID, *, tenant_id: UUID | None = None) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if tenant_id is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)
        return await self.session.scalar(stmt)

    async def find_by_username(
        self, username: str, *, exclude_id: UUID | None = None
    ) -> User | None:
        stmt = select(User).where(func.lower(User.username) == username.lower())
        if exclude_id is not None:
            stmt = stmt.where(User.id != exclude_id)
        return await self.session.scalar(stmt)

    async def find_by_email(self, email: str, *, exclude_id: UUID | None = None) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower())
        if exclude_id is not None:
            stmt = stmt.where(User.id != exclude_id)
        return await self.session.scalar(stmt)

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
