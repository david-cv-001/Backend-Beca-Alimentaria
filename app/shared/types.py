from enum import StrEnum


class Role(StrEnum):
    """Rol de un operador del sistema.

    En la base de datos y en el JWT se guarda en MAYÚSCULAS.
    En el JSON de la API se expone en PascalCase (``Superadmin``),
    que es lo que consume el frontend Angular.
    """

    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    CHECKER = "CHECKER"

    @property
    def api_value(self) -> str:
        """Formato expuesto al frontend: ``SUPERADMIN`` -> ``Superadmin``."""
        return self.value.capitalize()

    @classmethod
    def from_api(cls, value: str) -> "Role":
        """Convierte el formato del frontend a rol de dominio: ``Superadmin`` -> ``SUPERADMIN``."""
        return cls(value.upper())
