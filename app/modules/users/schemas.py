from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_serializer, field_validator

from app.modules.users.models import User
from app.shared.schemas import CamelModel
from app.shared.types import Role

USERNAME_PATTERN = r"^[a-zA-Z0-9._-]{3,30}$"
FULL_NAME_PATTERN = r"^[\p{L}\s.'-]{3,120}$"
PHONE_PATTERN = r"^[0-9+\-()\s]{10,15}$"
EMAIL_MAX_LENGTH = 120
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class UserWriteRequest(CamelModel):
    """Campos editables de un usuario (alta y actualización comparten contrato)."""

    full_name: str = Field(min_length=3, max_length=120, pattern=FULL_NAME_PATTERN)
    role: Role
    tenant_id: UUID | None = None
    phone: str = Field(pattern=PHONE_PATTERN)
    email: EmailStr
    active: bool = True

    @field_validator("full_name", "phone", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        # El correo se guarda en minúsculas (regla de negocio).
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        if len(normalized) > EMAIL_MAX_LENGTH:
            raise ValueError(f"El correo no puede superar los {EMAIL_MAX_LENGTH} caracteres")
        return normalized

    @field_validator("role", mode="before")
    @classmethod
    def _role_from_api(cls, value: object) -> object:
        # El frontend envía PascalCase ("Checker"); el dominio usa MAYÚSCULAS.
        return Role.from_api(value).value if isinstance(value, str) else value


class CreateUserRequest(UserWriteRequest):
    """Alta de usuario: añade el ``username``, que no es editable después."""

    username: str = Field(min_length=3, max_length=30, pattern=USERNAME_PATTERN)

    @field_validator("username", mode="before")
    @classmethod
    def _normalize_username(cls, value: object) -> object:
        # El username se guarda en minúsculas (regla de negocio).
        return value.strip().lower() if isinstance(value, str) else value

    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class UpdateUserRequest(UserWriteRequest):
    """PUT: reemplaza los campos editables; el ``password`` es opcional."""

    password: str | None = Field(
        default=None, min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class UserStatusRequest(CamelModel):
    active: bool


class UserResponse(CamelModel):
    id: UUID
    username: str
    full_name: str
    role: Role
    tenant_id: UUID | None = None
    tenant_name: str | None = None
    phone: str
    email: str
    active: bool
    created_at: datetime

    @field_serializer("role")
    def _role_to_api(self, value: Role) -> str:
        return value.api_value

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=Role(user.role),
            tenant_id=user.tenant_id,
            tenant_name=user.tenant.name if user.tenant is not None else None,
            phone=user.phone,
            email=user.email,
            active=user.active,
            created_at=user.created_at,
        )
