from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.modules.tenants import models as tenants_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401

TEST_DATABASE = "beca_alimentaria_test"


async def _ensure_test_database() -> None:
    """Crea la base de datos de test si no existe (idempotente)."""
    admin_url = make_url(settings.database_url).set(database="postgres")
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DATABASE}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DATABASE}"'))
    await engine.dispose()


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Sesión contra la BD de test, atada a una transacción que se revierte.

    Así los tests escriben sin dejar rastro y sin chocar con datos sembrados.
    """
    await _ensure_test_database()
    test_url = make_url(settings.database_url).set(database=TEST_DATABASE)
    engine = create_async_engine(test_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    connection = await engine.connect()
    transaction = await connection.begin()
    db_session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield db_session
    finally:
        await db_session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP que comparte la sesión del test (misma transacción)."""

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()
