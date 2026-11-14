from app.core.pagination import Pagination
from app.shared.schemas import CamelModel


class ApiResponse[T](CamelModel):
    """Envelope de éxito: toda respuesta exitosa va dentro de ``data``."""

    data: T
    pagination: Pagination | None = None


class ApiError(CamelModel):
    """Envelope de error que el frontend ya sabe leer."""

    process: str
    message: str
    errors: list[str] = []
