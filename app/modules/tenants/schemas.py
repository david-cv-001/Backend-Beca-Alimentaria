from datetime import datetime, time
from uuid import UUID

from pydantic import Field, ValidationInfo, field_serializer, field_validator

from app.shared.schemas import CamelModel

FOLIO_PATTERN = r"^[A-Z0-9][A-Z0-9-]{2,19}$"
NAME_PATTERN = r"^[\p{L}\p{N}\s.'&,-]{3,120}$"
REPRESENTATIVE_PATTERN = r"^[\p{L}\s.'-]{3,120}$"

MEAL_TIME_FIELDS = ("breakfast_start", "breakfast_end", "lunch_start", "lunch_end")

# Mensaje de usuario (español) para una ventana de servicio invertida.
END_BEFORE_START_MESSAGE = "La hora de fin debe ser posterior a la hora de inicio"


class TenantWriteRequest(CamelModel):
    """Campos escribibles de una cafetería (alta y actualización comparten contrato)."""

    folio: str = Field(min_length=3, max_length=20, pattern=FOLIO_PATTERN)
    name: str = Field(min_length=3, max_length=120, pattern=NAME_PATTERN)
    representative: str = Field(min_length=3, max_length=120, pattern=REPRESENTATIVE_PATTERN)

    # Horarios de servicio, en hora local de la cafetería. Se envían como "HH:MM"
    # (también se acepta "HH:MM:SS"); la API siempre responde "HH:MM".
    breakfast_start: time = Field(examples=["07:00"])
    breakfast_end: time = Field(examples=["10:00"])
    lunch_start: time = Field(examples=["13:00"])
    lunch_end: time = Field(examples=["16:00"])

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

    @field_validator("breakfast_end")
    @classmethod
    def _breakfast_end_after_start(cls, value: time, info: ValidationInfo) -> time:
        start = info.data.get("breakfast_start")
        if isinstance(start, time) and value <= start:
            raise ValueError(END_BEFORE_START_MESSAGE)
        return value

    @field_validator("lunch_end")
    @classmethod
    def _lunch_end_after_start(cls, value: time, info: ValidationInfo) -> time:
        start = info.data.get("lunch_start")
        if isinstance(start, time) and value <= start:
            raise ValueError(END_BEFORE_START_MESSAGE)
        return value


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
    breakfast_start: time
    breakfast_end: time
    lunch_start: time
    lunch_end: time
    active: bool
    created_at: datetime

    @field_serializer(*MEAL_TIME_FIELDS)
    def _serialize_meal_time(self, value: time) -> str:
        """Expone la hora como ``"HH:MM"`` (lo que espera el frontend)."""
        return value.strftime("%H:%M")
