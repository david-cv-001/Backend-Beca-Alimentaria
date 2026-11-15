from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.errors import ForbiddenException, UnauthorizedException, route_process
from app.core.security import decode_token
from app.db.session import SessionDep
from app.db.tenancy import TenantContext
from app.modules.users.models import User
from app.shared.types import Role

bearer_scheme = HTTPBearer(auto_error=False)
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


async def get_current_user(
    request: Request,
    credentials: BearerDep,
    session: SessionDep,
) -> User:
    """Resuelve el usuario a partir del Bearer token.

    El rol **no** se toma del token: se recarga el usuario de la BD para que un
    cambio de rol o una desactivación surtan efecto de inmediato.
    """
    process = route_process(request)

    if credentials is None:
        raise UnauthorizedException("Credenciales no proporcionadas", process=process)

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise UnauthorizedException("Sesión no válida o expirada", process=process) from exc

    subject = payload.get("sub")
    try:
        user_id = UUID(subject)
    except (TypeError, ValueError) as exc:
        raise UnauthorizedException("Sesión no válida", process=process) from exc

    user = await session.scalar(select(User).where(User.id == user_id))
    if user is None or not user.active:
        raise UnauthorizedException("Sesión no válida", process=process)

    if user.tenant_id is not None and (user.tenant is None or not user.tenant.active):
        raise UnauthorizedException("La cafetería está desactivada", process=process)

    # Aislamiento multi-tenant: el contexto alimenta los filtros del repositorio.
    TenantContext.set(user.tenant_id)
    return user


# Alias para inyectar el usuario autenticado en los routers.
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[..., Awaitable[User]]:
    """Genera una dependencia que exige que el usuario tenga uno de esos roles."""
    allowed = {role.value for role in roles}

    async def _guard(request: Request, user: CurrentUser) -> User:
        if user.role not in allowed:
            raise ForbiddenException(process=route_process(request))
        return user

    return _guard
