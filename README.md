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

## Levantar todo con Docker Compose

Forma recomendada de correr el proyecto completo (base de datos + API) sin instalar `uv` localmente.

### Servicios

| Contenedor | Estado | Puerto |
| --- | --- | --- |
| `beca-alimentaria-api` | Up | `8080` |
| `beca-alimentaria-postgres` | Up (healthy) | `5432` |

El contenedor `api` corre `alembic upgrade head` automáticamente al arrancar.

### Ciclo de trabajo

```bash
cd /home/davidcv/proyectos/Backend_Beca_Alimentaria

# Levantar todo
make up                 # o: docker compose up -d

# Ver logs en vivo (con --reload los cambios de código se recargan solos)
docker compose logs -f api

# Detener todo
make down               # o: docker compose down
```

### Verificación

- `http://localhost:8080/health` → `{"status":"ok"}`
- `http://localhost:8080/docs` → Swagger
- Envelope de errores: `{"process":"API_ERROR","message":"Not Found","errors":[]}`
- Usuario inicial: `superadmin@beca.com` / `admin123`

> El seed **no** es automático: si borras la base de datos (`docker compose down -v`), vuelve a crearla con
> `docker compose exec api uv run python scripts/seed_superadmin.py`.

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
