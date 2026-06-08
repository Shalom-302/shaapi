# Architecture

shaapi follows a clean, layered architecture inspired by
*fastapi-best-architecture*, trimmed to a lean core.

## Project layout

```
my_api/
├── docker-compose.yml            # base stack (api, postgres, redis, minio)
├── docker-compose.override.yml   # dev: source bind-mount + hot-reload
├── docker-compose.monitoring.yml # opt-in observability
├── docker-run.sh                 # orchestration wrapper
├── Dockerfile                    # multi-stage slim image (built with uv)
├── pyproject.toml                # dependencies (uv)
├── .env / .env.template          # configuration
└── backend/
    ├── main.py                   # app entry point (parent app + lifespan)
    ├── core/
    │   ├── conf.py               # settings (pydantic-settings)
    │   ├── registrar.py          # app factory: middleware, routers, lifespan
    │   └── path_conf.py
    ├── app/admin/                # the "admin" sub-application
    │   ├── api/v1/               # routers (auto-discovered)
    │   ├── schema/               # Pydantic schemas
    │   └── service/              # business logic
    ├── models/                   # SQLAlchemy models
    ├── crud/                     # data access (CRUDBase / sqlalchemy-crud-plus)
    ├── common/                   # security, responses, exceptions, storage…
    ├── middleware/               # JWT, i18n, opera-log, state, trace…
    ├── database/                 # Postgres + Redis clients
    └── alembic/                  # migrations
```

## The layers

A request flows through clear layers, each with one responsibility:

```
HTTP → router (api/v1) → service → crud → model (DB)
              │             │        │
            schema       business   data
          validation      rules     access
```

- **models/** — SQLAlchemy 2 declarative models (the database tables).
- **schema/** — Pydantic v2 models for request/response validation.
- **crud/** — thin data-access classes extending `CRUDBase`
  (`sqlalchemy-crud-plus`): `select_model`, `create_model`, `update_model`…
- **service/** — business logic, transactions (`async_db_session.begin()`),
  authorization checks.
- **api/v1/** — FastAPI routers returning a unified `ResponseModel`.

## Router auto-discovery

Any `*.py` in `app/admin/api/v1/` that defines a `router` is **loaded
automatically** (`backend/app/__init__.py`). Add a file, get endpoints — no
central registry to edit.

## The app & its lifespan

`backend/main.py` builds a thin **parent** FastAPI app that mounts the feature
sub-apps (currently `/admin`). The parent owns the **lifespan** (creating DB
tables in dev, opening Redis, initializing the rate limiter) because Starlette
does not run the lifespan of *mounted* sub-applications.

## Configuration

`core/conf.py` defines all settings with safe development defaults, so the app
boots with an empty `.env`. Override via environment variables / `.env`. Key
flags:

| Setting                 | Default | Meaning                                            |
|-------------------------|---------|----------------------------------------------------|
| `ENVIRONMENT`           | `dev`   | `dev` enables reload; `prod` serves baked code      |
| `DB_AUTO_CREATE`        | `true`  | Auto-create tables on startup (dev). Off in prod.   |
| `OBSERVABILITY_ENABLED` | `false` | Prometheus/OpenTelemetry (opt-in)                   |

## Database & migrations

- **Dev**: tables are auto-created on startup (`DB_AUTO_CREATE=true`) for a
  zero-friction first run.
- **Prod**: set `DB_AUTO_CREATE=false` and use Alembic migrations
  (`alembic upgrade head`, run automatically by the entrypoint). Author new
  migrations with `./docker-run.sh makemigrations "message"`.

Migrations are the source of truth and are committed to your repo.

## Built in

- **Auth**: JWT (access + refresh), register/login, `DependsJwtAuth`.
- **RBAC**: Casbin policies; users, roles, permissions.
- **Storage**: MinIO / S3 / GCS via a common interface.
- **Observability** (opt-in): Prometheus metrics, OpenTelemetry traces,
  Grafana + Tempo + Loki.
- **Cross-cutting**: request IDs, operation logs, login logs, i18n,
  rate limiting, unified responses and error handling.

## Tech stack

FastAPI · SQLAlchemy 2 (async) · Pydantic v2 · Alembic · PostgreSQL · Redis ·
Casbin · MinIO · uv · Docker. See [Create a feature](create-a-feature.md) to
build on top of it.
