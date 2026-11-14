"""Crea el primer superadministrador a partir de las variables de entorno.

Idempotente: si ya existe un SUPERADMIN, no hace nada.
Ejecución: ``uv run python scripts/seed_superadmin.py``
"""

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.users.models import User
from app.shared.types import Role


async def main() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(User).where(User.role == Role.SUPERADMIN.value))
        if existing is not None:
            print(f"Ya existe un SUPERADMIN ({existing.username}). Nada que hacer.")
            return

        admin = User(
            tenant_id=None,
            role=Role.SUPERADMIN.value,
            username=settings.first_superadmin_username.lower(),
            email=settings.first_superadmin_email.lower(),
            password_hash=hash_password(settings.first_superadmin_password),
            full_name="Super Administrador",
            phone="0000000000",
            active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"SUPERADMIN creado: {admin.username}")


if __name__ == "__main__":
    asyncio.run(main())
