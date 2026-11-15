from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.pagination import PageParams, Pagination
from app.db.session import SessionDep
from app.modules.auth.dependencies import require_roles
from app.modules.tenants.repository import TenantRepository
from app.modules.tenants.schemas import (
    CreateTenantRequest,
    TenantResponse,
    TenantStatusRequest,
    UpdateTenantRequest,
)
from app.modules.tenants.service import TenantService
from app.modules.users.models import User
from app.shared.responses import ApiResponse, PaginatedResponse
from app.shared.types import Role

router = APIRouter(prefix="/tenants", tags=["tenants"])

SuperadminDep = Annotated[User, Depends(require_roles(Role.SUPERADMIN))]


class TenantPageParams(PageParams):
    default_sort = "name:asc"


TenantPageParamsDep = Annotated[TenantPageParams, Depends(TenantPageParams)]


def get_tenant_service(session: SessionDep) -> TenantService:
    return TenantService(TenantRepository(session))


TenantServiceDep = Annotated[TenantService, Depends(get_tenant_service)]


@router.get(
    "",
    response_model=PaginatedResponse[TenantResponse],
    name="TENANT_LIST",
    summary="Listar cafeterías",
)
async def list_tenants(
    _: SuperadminDep,
    params: TenantPageParamsDep,
    service: TenantServiceDep,
) -> PaginatedResponse[TenantResponse]:
    page = await service.list_tenants(params)
    return PaginatedResponse(
        data=[TenantResponse.model_validate(tenant) for tenant in page.items],
        pagination=Pagination.build(params, page.total),
    )


@router.get(
    "/{tenant_id}",
    response_model=ApiResponse[TenantResponse],
    name="TENANT_GET",
    summary="Obtener una cafetería",
)
async def get_tenant(
    tenant_id: UUID,
    _: SuperadminDep,
    service: TenantServiceDep,
) -> ApiResponse[TenantResponse]:
    tenant = await service.get_tenant(tenant_id)
    return ApiResponse(data=TenantResponse.model_validate(tenant))


@router.post(
    "",
    response_model=ApiResponse[TenantResponse],
    status_code=status.HTTP_201_CREATED,
    name="TENANT_CREATE",
    summary="Crear una cafetería",
)
async def create_tenant(
    payload: CreateTenantRequest,
    _: SuperadminDep,
    service: TenantServiceDep,
) -> ApiResponse[TenantResponse]:
    tenant = await service.create_tenant(payload)
    return ApiResponse(data=TenantResponse.model_validate(tenant))


@router.put(
    "/{tenant_id}",
    response_model=ApiResponse[TenantResponse],
    name="TENANT_UPDATE",
    summary="Actualizar una cafetería",
)
async def update_tenant(
    tenant_id: UUID,
    payload: UpdateTenantRequest,
    _: SuperadminDep,
    service: TenantServiceDep,
) -> ApiResponse[TenantResponse]:
    tenant = await service.update_tenant(tenant_id, payload)
    return ApiResponse(data=TenantResponse.model_validate(tenant))


@router.patch(
    "/{tenant_id}/status",
    response_model=ApiResponse[TenantResponse],
    name="TENANT_STATUS",
    summary="Cambiar el estado de una cafetería",
)
async def change_tenant_status(
    tenant_id: UUID,
    payload: TenantStatusRequest,
    _: SuperadminDep,
    service: TenantServiceDep,
) -> ApiResponse[TenantResponse]:
    tenant = await service.change_status(tenant_id, payload.active)
    return ApiResponse(data=TenantResponse.model_validate(tenant))
