from contextvars import ContextVar
from typing import Optional
from uuid import UUID


tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)


class TenantContext:
    NO_TENANT = UUID(int=0)

    @staticmethod
    def get() -> Optional[UUID]:
        return tenant_id_ctx.get()

    @staticmethod
    def set(tenant_id: UUID | None) -> None:
        tenant_id_ctx.set(tenant_id)

    @staticmethod
    def clear() -> None:
        tenant_id_ctx.set(None)

    @staticmethod
    def must_get() -> UUID:
        tid = tenant_id_ctx.get()
        if tid is None:
            return TenantContext.NO_TENANT
        return tid
