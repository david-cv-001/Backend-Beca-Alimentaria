from dataclasses import dataclass
from typing import Annotated

from fastapi import Query

from app.shared.schemas import CamelModel


class PageParams:
    """Parámetros de paginación de los listados.

    El frontend envía ``?page=1&pageSize=10&sortBy=name:asc``.
    ``sortBy`` llega como ``campo:dirección``; la validación de que el campo
    sea uno permitido la hace cada repositorio. Cada recurso puede cambiar el
    orden por defecto sobreescribiendo ``default_sort``.
    """

    default_sort: str = "created_at:desc"

    def __init__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100, alias="pageSize")] = 10,
        sort_by: Annotated[str | None, Query(alias="sortBy")] = None,
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.sort_field, self.sort_direction = self._parse_sort(sort_by or self.default_sort)

    @staticmethod
    def _parse_sort(value: str) -> tuple[str, str]:
        field, _, direction = value.partition(":")
        direction = direction.strip().upper()
        return field.strip(), direction if direction in {"ASC", "DESC"} else "ASC"

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Pagination(CamelModel):
    """Bloque ``pagination`` que acompaña a los listados."""

    page: int
    page_size: int
    sort_by: str
    sort_direction: str
    total_elements: int
    total_pages: int

    @classmethod
    def build(cls, params: PageParams, total: int) -> "Pagination":
        total_pages = -(-total // params.page_size) if params.page_size else 0
        return cls(
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_field,
            sort_direction=params.sort_direction,
            total_elements=total,
            total_pages=total_pages,
        )


@dataclass
class Page[T]:
    """Resultado interno de un listado paginado (capa de servicio).

    Es un ``dataclass`` y no un modelo Pydantic: transporta entidades ORM que el
    router convierte a ``TenantResponse`` / ``UserResponse`` antes de responder.
    """

    items: list[T]
    total: int
