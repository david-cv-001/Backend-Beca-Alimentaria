from sqlalchemy import Boolean, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BaseAuditMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, BaseAuditMixin, Base):
    """Cafetería. Su ``id`` es el discriminador de aislamiento del resto del sistema."""

    __tablename__ = "tenants"

    folio: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    representative: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))

    __table_args__ = (
        Index("uq_tenants_folio_ci", text("lower(folio)"), unique=True),
        Index("uq_tenants_name_ci", text("lower(name)"), unique=True),
        Index("ix_tenants_active", "active"),
    )

    def __repr__(self) -> str:
        return f"<Tenant folio={self.folio!r} name={self.name!r}>"
