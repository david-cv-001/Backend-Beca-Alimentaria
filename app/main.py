from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.modules.auth.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    try:
        from app.modules.biometrics.loader import preload_models

        await preload_models()
    except Exception:
        pass
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Routers de los módulos. Se agregan a medida que se implementan.
app.include_router(auth_router, prefix=settings.api_v1_prefix)
#   app.include_router(tenants_router, prefix=settings.api_v1_prefix)
#   app.include_router(users_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
