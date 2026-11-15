from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.pagination import PageParams, Pagination
from app.db.session import SessionDep
from app.modules.auth.dependencies import require_roles
from app.modules.tenants.repository import TenantRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserStatusRequest,
)
from app.modules.users.service import UserService
from app.shared.responses import ApiResponse, PaginatedResponse
from app.shared.types import Role

router = APIRouter(prefix="/users", tags=["users"])

# El listado y la gestión de usuarios requieren SUPERADMIN o ADMIN; las reglas
# finas (qué rol y qué tenant) viven en el servicio.
StaffDep = Annotated[User, Depends(require_roles(Role.SUPERADMIN, Role.ADMIN))]


class UserPageParams(PageParams):
    default_sort = "username:asc"


UserPageParamsDep = Annotated[UserPageParams, Depends(UserPageParams)]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(UserRepository(session), TenantRepository(session))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    name="USER_LIST",
    summary="Listar usuarios",
)
async def list_users(
    requester: StaffDep,
    params: UserPageParamsDep,
    service: UserServiceDep,
) -> PaginatedResponse[UserResponse]:
    page = await service.list_users(requester, params)
    return PaginatedResponse(
        data=[UserResponse.from_user(user) for user in page.items],
        pagination=Pagination.build(params, page.total),
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    name="USER_GET",
    summary="Obtener un usuario",
)
async def get_user(
    user_id: UUID,
    requester: StaffDep,
    service: UserServiceDep,
) -> ApiResponse[UserResponse]:
    user = await service.get_user(requester, user_id)
    return ApiResponse(data=UserResponse.from_user(user))


@router.post(
    "",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    name="USER_CREATE",
    summary="Crear un usuario",
)
async def create_user(
    payload: CreateUserRequest,
    requester: StaffDep,
    service: UserServiceDep,
) -> ApiResponse[UserResponse]:
    user = await service.create_user(requester, payload)
    return ApiResponse(data=UserResponse.from_user(user))


@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    name="USER_UPDATE",
    summary="Actualizar un usuario",
)
async def update_user(
    user_id: UUID,
    payload: UpdateUserRequest,
    requester: StaffDep,
    service: UserServiceDep,
) -> ApiResponse[UserResponse]:
    user = await service.update_user(requester, user_id, payload)
    return ApiResponse(data=UserResponse.from_user(user))


@router.patch(
    "/{user_id}/status",
    response_model=ApiResponse[UserResponse],
    name="USER_STATUS",
    summary="Cambiar el estado de un usuario",
)
async def change_user_status(
    user_id: UUID,
    payload: UserStatusRequest,
    requester: StaffDep,
    service: UserServiceDep,
) -> ApiResponse[UserResponse]:
    user = await service.change_status(requester, user_id, payload.active)
    return ApiResponse(data=UserResponse.from_user(user))
