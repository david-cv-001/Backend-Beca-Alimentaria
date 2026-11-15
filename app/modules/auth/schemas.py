from uuid import UUID

from pydantic import Field

from app.modules.users.models import User
from app.shared.schemas import CamelModel
from app.shared.types import Role


class LoginRequest(CamelModel):
    """Credenciales de acceso. El identificador puede ser username o email."""

    username_or_email: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class AuthUser(CamelModel):
    """Usuario tal como lo expone la sesión (el rol va en array, como espera el front)."""

    id: UUID
    username: str
    full_name: str
    email: str
    roles: list[str]
    tenant_id: UUID | None = None
    tenant_name: str | None = None

    @classmethod
    def from_user(cls, user: User) -> "AuthUser":
        return cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            roles=[Role(user.role).api_value],
            tenant_id=user.tenant_id,
            tenant_name=user.tenant.name if user.tenant is not None else None,
        )


class LoginResponse(CamelModel):
    access_token: str
    user: AuthUser
