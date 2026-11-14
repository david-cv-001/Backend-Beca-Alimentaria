from contextvars import ContextVar
from uuid import UUID

tenant_id_ctx: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)


class TenantContext:
    NO_TENANT = UUID(int=0)

    @staticmethod
    def get() -> UUID | None:
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
