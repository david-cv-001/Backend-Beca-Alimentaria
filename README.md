# Backend Beca Alimentaria

Backend para el sistema de asistencia con reconocimiento facial para becas alimentarias.

## Stack
- Python 3.12
- FastAPI
- PostgreSQL 16 + pgvector
- SQLAlchemy 2.0 (async)
- Alembic
- Pydantic v2
- PyJWT + pwdlib (argon2)
- DeepFace (opcional)

## Alcance inicial
- Módulo de Tenants (Cafeterías)
- Módulo de Usuarios y Roles (Superadmin, Admin, Checker)
- Autenticación JWT propia
- Aislamiento multi-tenant por discriminador
- Preparado para módulo de Estudiantes + biometría facial

## Inicio rápido

```bash
# Crear .env
make env

# Levantar infraestructura (Postgres + pgvector)
make up-infra

# Instalar dependencias
make install

# Ejecutar migraciones
make migrate

# Crear el primer superadmin (idempotente)
make seed

# Ejecutar app (puerto 8080)
uv run uvicorn app.main:app --reload --port 8080
```

Swagger: http://localhost:8080/docs

## Documentación
- [Convenciones](docs/CONVENTIONS.md)
- [Vocabulario dominio](docs/vocabulary.md)
- [ADR's](docs/adr/)
- Especificación de Tenants y Usuarios: `/home/davidcv/proyectos/documentacion/beca_alimentaria/`

## Notas
- Todo el código va en **inglés**. Excepciones: mensajes de error al usuario final en español (concentrados en handlers).
- Aislamiento por tenant aplicado automáticamente. No filtrar tenant manualmente en services.
- Consultas nativas deben filtrar `tenant_id` explícitamente.
- Embeddings biométricos se almacenarán con `pgvector` (vector(512)), nunca imágenes originales.
