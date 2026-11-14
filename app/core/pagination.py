from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.shared.schemas import CamelModel


class PageParams:
    """Parámetros de paginación de los listados.

    El frontend envía ``?page=1&pageSize=10&sortBy=name:asc``.
    ``sortBy`` llega como ``campo:dirección``; la validación de que el campo
    sea uno permitido la hace cada repositorio.
    """

    def __init__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100, alias="pageSize")] = 10,
        sort_by: Annotated[str, Query(alias="sortBy")] = "created_at:desc",
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.sort_field, self.sort_direction = self._parse_sort(sort_by)

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


class Page[T](BaseModel):
    """Resultado interno de un listado paginado."""

    items: list[T]
    total: int
