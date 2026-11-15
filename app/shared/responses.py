from app.core.pagination import Pagination
from app.shared.schemas import CamelModel


class ApiResponse[T](CamelModel):
    """Envelope de éxito para una respuesta de un solo recurso."""

    data: T


class PaginatedResponse[T](CamelModel):
    """Envelope de éxito para un listado: añade el bloque ``pagination``."""

    data: list[T]
    pagination: Pagination


class ApiError(CamelModel):
    """Envelope de error que el frontend ya sabe leer."""

    process: str
    message: str
    errors: list[str] = []
