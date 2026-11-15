from uuid import UUID

from app.core.errors import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.pagination import Page, PageParams
from app.core.security import hash_password
from app.modules.tenants.models import Tenant
from app.modules.tenants.repository import TenantRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import CreateUserRequest, UpdateUserRequest
from app.shared.types import Role


class UserService:
    """Reglas de negocio de usuarios.

    Un ``ADMIN`` solo gestiona a los ``CHECKER`` de su propia cafetería; un
    ``SUPERADMIN`` gestiona cualquier usuario de cualquier cafetería. Nadie
    puede crear ni asignar el rol ``SUPERADMIN`` por API.
    """

    def __init__(self, repository: UserRepository, tenant_repository: TenantRepository) -> None:
        self.repository = repository
        self.tenant_repository = tenant_repository

    async def list_users(self, requester: User, params: PageParams) -> Page[User]:
        tenant_id = self._scope(requester)
        users = await self.repository.find_all(
            tenant_id=tenant_id,
            offset=params.offset,
            limit=params.limit,
            sort_field=params.sort_field,
            sort_direction=params.sort_direction,
        )
        total = await self.repository.count(tenant_id=tenant_id)
        return Page(items=users, total=total)

    async def get_user(self, requester: User, user_id: UUID) -> User:
        user = await self.repository.find_by_id(user_id, tenant_id=self._scope(requester))
        if user is None:
            raise NotFoundException("No existe el usuario solicitado")
        return user

    async def create_user(self, requester: User, data: CreateUserRequest) -> User:
        role, tenant = await self._resolve_scope(requester, data.role, data.tenant_id)
        await self._ensure_unique(username=data.username, email=data.email)
        user = User(
            tenant=tenant,
            role=role.value,
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            active=data.active,
        )
        await self.repository.add(user)
        await self.repository.session.commit()
        return user

    async def update_user(self, requester: User, user_id: UUID, data: UpdateUserRequest) -> User:
        user = await self.get_user(requester, user_id)
        self._ensure_manageable(requester, user)
        role, tenant = await self._resolve_scope(requester, data.role, data.tenant_id, target=user)
        await self._ensure_unique(email=data.email, exclude_id=user_id)

        user.tenant = tenant
        user.role = role.value
        user.full_name = data.full_name
        user.phone = data.phone
        user.email = data.email
        user.active = data.active
        if data.password:
            user.password_hash = hash_password(data.password)

        await self.repository.session.commit()
        return user

    async def change_status(self, requester: User, user_id: UUID, active: bool) -> User:
        user = await self.get_user(requester, user_id)
        self._ensure_manageable(requester, user)
        user.active = active
        await self.repository.session.commit()
        return user

    @staticmethod
    def _scope(requester: User) -> UUID | None:
        """``SUPERADMIN`` opera sin filtro; ``ADMIN`` queda limitado a su cafetería."""
        if requester.role == Role.SUPERADMIN.value:
            return None
        return requester.tenant_id

    @staticmethod
    def _ensure_manageable(requester: User, target: User) -> None:
        """Un ``ADMIN`` solo puede gestionar usuarios ``CHECKER`` de su cafetería."""
        if requester.role == Role.ADMIN.value and target.role != Role.CHECKER.value:
            raise ForbiddenException("Un administrador solo puede gestionar usuarios Checker")

    async def _resolve_scope(
        self,
        requester: User,
        role: Role,
        tenant_id: UUID | None,
        *,
        target: User | None = None,
    ) -> tuple[Role, Tenant | None]:
        """Valida el rol solicitado y resuelve la cafetería destino del usuario.

        - El rol ``SUPERADMIN`` no se puede *asignar* por API; solo se conserva
          al editar un usuario que ya lo tiene (p. ej. el propio perfil).
        - Un ``ADMIN`` solo puede asignar ``CHECKER`` y en su propia cafetería.
        - Un ``SUPERADMIN`` debe indicar la cafetería del usuario.
        """
        if role is Role.SUPERADMIN:
            keeps_superadmin = (
                requester.role == Role.SUPERADMIN.value
                and target is not None
                and target.role == Role.SUPERADMIN.value
            )
            if not keeps_superadmin:
                raise ForbiddenException("No está permitido crear o asignar el rol Superadmin")
            return Role.SUPERADMIN, None

        if requester.role == Role.ADMIN.value:
            if role is not Role.CHECKER:
                raise ForbiddenException("Un administrador solo puede gestionar usuarios Checker")
            # El tenant del ADMIN se impone aunque envíe otro (o ninguno).
            return Role.CHECKER, await self._get_tenant(requester.tenant_id)

        if tenant_id is None:
            raise BadRequestException("Debe indicar la cafetería del usuario")
        return role, await self._get_tenant(tenant_id)

    async def _get_tenant(self, tenant_id: UUID | None) -> Tenant | None:
        if tenant_id is None:
            return None
        tenant = await self.tenant_repository.find_by_id(tenant_id)
        if tenant is None:
            raise BadRequestException("La cafetería indicada no existe")
        return tenant

    async def _ensure_unique(
        self, *, username: str | None = None, email: str, exclude_id: UUID | None = None
    ) -> None:
        if username is not None and (
            await self.repository.find_by_username(username, exclude_id=exclude_id) is not None
        ):
            raise ConflictException("Ya existe un usuario con ese nombre de usuario")
        if await self.repository.find_by_email(email, exclude_id=exclude_id) is not None:
            raise ConflictException("Ya existe un usuario con ese correo")
