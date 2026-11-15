from uuid import UUID

from app.core.errors import ConflictException, NotFoundException
from app.core.pagination import Page, PageParams
from app.modules.tenants.models import Tenant
from app.modules.tenants.repository import TenantRepository
from app.modules.tenants.schemas import CreateTenantRequest, UpdateTenantRequest


class TenantService:
    """Reglas de negocio de cafeterías."""

    def __init__(self, repository: TenantRepository) -> None:
        self.repository = repository

    async def list_tenants(self, params: PageParams) -> Page[Tenant]:
        tenants = await self.repository.find_all(
            offset=params.offset,
            limit=params.limit,
            sort_field=params.sort_field,
            sort_direction=params.sort_direction,
        )
        total = await self.repository.count()
        return Page(items=tenants, total=total)

    async def get_tenant(self, tenant_id: UUID) -> Tenant:
        tenant = await self.repository.find_by_id(tenant_id)
        if tenant is None:
            raise NotFoundException("No existe la cafetería solicitada")
        return tenant

    async def create_tenant(self, data: CreateTenantRequest) -> Tenant:
        await self._ensure_unique(folio=data.folio, name=data.name)
        tenant = Tenant(
            folio=data.folio,
            name=data.name,
            representative=data.representative,
            breakfast_start=data.breakfast_start,
            breakfast_end=data.breakfast_end,
            lunch_start=data.lunch_start,
            lunch_end=data.lunch_end,
            active=data.active,
        )
        await self.repository.add(tenant)
        await self.repository.session.commit()
        return tenant

    async def update_tenant(self, tenant_id: UUID, data: UpdateTenantRequest) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        await self._ensure_unique(folio=data.folio, name=data.name, exclude_id=tenant_id)

        tenant.folio = data.folio
        tenant.name = data.name
        tenant.representative = data.representative
        tenant.breakfast_start = data.breakfast_start
        tenant.breakfast_end = data.breakfast_end
        tenant.lunch_start = data.lunch_start
        tenant.lunch_end = data.lunch_end
        tenant.active = data.active
        if not data.active:
            await self.repository.deactivate_users(tenant_id)

        await self.repository.session.commit()
        return tenant

    async def change_status(self, tenant_id: UUID, active: bool) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        tenant.active = active
        if not active:
            await self.repository.deactivate_users(tenant_id)
        await self.repository.session.commit()
        return tenant

    async def _ensure_unique(
        self, *, folio: str, name: str, exclude_id: UUID | None = None
    ) -> None:
        if await self.repository.find_by_folio(folio, exclude_id=exclude_id) is not None:
            raise ConflictException("Ya existe una cafetería con ese folio")
        if await self.repository.find_by_name(name, exclude_id=exclude_id) is not None:
            raise ConflictException("Ya existe una cafetería con ese nombre")
