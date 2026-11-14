import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseAuditMixin, UUIDPrimaryKeyMixin
from app.modules.tenants.models import Tenant


class User(UUIDPrimaryKeyMixin, BaseAuditMixin, Base):
    """Operador del sistema.

    ``SUPERADMIN`` no pertenece a ninguna cafetería; ``ADMIN`` y ``CHECKER`` sí.
    El rol se guarda en MAYÚSCULAS y se expone en PascalCase desde los schemas.
    """

    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped[Tenant | None] = relationship(lazy="joined")

    __table_args__ = (
        Index("uq_users_username_ci", text("lower(username)"), unique=True),
        Index("uq_users_email_ci", text("lower(email)"), unique=True),
        Index("ix_users_tenant_id", "tenant_id"),
        Index("ix_users_role", "role"),
        Index("ix_users_active", "active"),
        CheckConstraint("role IN ('SUPERADMIN', 'ADMIN', 'CHECKER')", name="ck_users_role"),
        CheckConstraint(
            "(role = 'SUPERADMIN' AND tenant_id IS NULL) "
            "OR (role IN ('ADMIN', 'CHECKER') AND tenant_id IS NOT NULL)",
            name="ck_users_tenant_by_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<User username={self.username!r} role={self.role!r}>"
