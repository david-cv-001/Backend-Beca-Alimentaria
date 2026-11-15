from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedException
from app.core.security import verify_password
from app.modules.users.models import User

PROCESS = "AUTH_LOGIN"


async def authenticate(session: AsyncSession, username_or_email: str, password: str) -> User:
    """Valida credenciales y devuelve el usuario.

    Lanza 401 si el usuario no existe, la contraseña no coincide, la cuenta está
    inactiva o la cafetería del usuario está inactiva. Un mismo mensaje evita
    revelar cuál de los casos ocurrió.
    """
    identifier = username_or_email.strip().lower()
    user = await session.scalar(
        select(User).where(
            or_(
                func.lower(User.username) == identifier,
                func.lower(User.email) == identifier,
            )
        )
    )

    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedException("Usuario o contraseña incorrectos", process=PROCESS)

    if not user.active:
        raise UnauthorizedException("La cuenta está desactivada", process=PROCESS)

    if user.tenant_id is not None and (user.tenant is None or not user.tenant.active):
        raise UnauthorizedException("La cafetería está desactivada", process=PROCESS)

    user.last_login_at = datetime.now(UTC)
    await session.commit()
    return user
