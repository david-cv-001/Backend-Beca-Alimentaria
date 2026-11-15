from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.shared.schemas import CamelModel

FOLIO_PATTERN = r"^[A-Z0-9][A-Z0-9-]{2,19}$"
NAME_PATTERN = r"^[\p{L}\p{N}\s.'&,-]{3,120}$"
REPRESENTATIVE_PATTERN = r"^[\p{L}\s.'-]{3,120}$"


class TenantWriteRequest(CamelModel):
    """Campos escribibles de una cafetería (alta y actualización comparten contrato)."""

    folio: str = Field(min_length=3, max_length=20, pattern=FOLIO_PATTERN)
    name: str = Field(min_length=3, max_length=120, pattern=NAME_PATTERN)
    representative: str = Field(min_length=3, max_length=120, pattern=REPRESENTATIVE_PATTERN)
    active: bool = True

    @field_validator("folio", mode="before")
    @classmethod
    def _normalize_folio(cls, value: object) -> object:
        # El folio se guarda en mayúsculas (regla de negocio); se normaliza antes
        # de validar el patrón para aceptar entradas en minúsculas.
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("name", "representative", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CreateTenantRequest(TenantWriteRequest):
    """Alta de cafetería."""


class UpdateTenantRequest(TenantWriteRequest):
    """PUT: reemplaza todos los campos."""


class TenantStatusRequest(CamelModel):
    active: bool


class TenantResponse(CamelModel):
    id: UUID
    folio: str
    name: str
    representative: str
    active: bool
    created_at: datetime
