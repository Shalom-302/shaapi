# shaapi

A lean, batteries-included **FastAPI** backend, generated with
[{{cli}}](https://github.com/Shalom-302/{{cli}}). Async SQLAlchemy + Alembic,
Postgres, Redis, JWT auth and Casbin RBAC, file storage, i18n and a
one-command Docker workflow — ready to build on.

> This project was scaffolded by `{{cli}}`. The `{{cli}}` command is also your
> day-to-day runner: it wraps `docker compose` directly, so the same commands
> work on **Windows, macOS and Linux** (no bash required).

## Quick start

```bash
{{cli}} up              # build + start the whole stack (dev: hot-reload)
{{cli}} db apply        # apply database migrations
{{cli}} auth init       # create an admin user to log into Swagger
{{cli}} storage init    # create the object-storage bucket
```

Then open:

- **API**: http://localhost:8000
- **Swagger**: http://localhost:8000/admin/api/v1/docs

> On Linux/macOS you can use the bundled `./docker-run.sh` instead of `{{cli}}`
> if you prefer a plain shell script — both drive the same Docker stack.

## Commands

Everything runs through `{{cli}}` (cross-platform) — no need to memorize raw
`docker compose` incantations. Commands are grouped by domain:

**Lifecycle**

```bash
{{cli}} up [--monitoring] [--prod]   # build + start (monitoring/prod optional)
{{cli}} down                         # stop and remove containers
{{cli}} logs [service]               # tail logs (e.g. {{cli}} logs api)
{{cli}} restart [service]            # restart all, or one service
{{cli}} ps                           # container status
{{cli}} shell                        # bash inside the api container
{{cli}} redis                        # redis-cli inside Redis
```

**Database (`db`)**

```bash
{{cli}} db generate --message "add posts table"   # autogenerate a migration
{{cli}} db apply                                   # alembic upgrade head
{{cli}} db preview                                 # SQL that apply would run
{{cli}} db pending                                 # current revision vs. head
{{cli}} db shell                                   # psql inside Postgres
```

**Auth (`auth`) & Storage (`storage`)**

```bash
{{cli}} auth init      # create an admin user (email + password)
{{cli}} storage init   # ensure the MinIO/S3 bucket exists
```

The equivalent `./docker-run.sh` subcommands exist for shell users on Unix
(`up`, `down`, `logs`, `migrate`, `makemigrations`, `shell`, …).

## What's inside

- **FastAPI** (async) with a layered architecture (`app/`, `common/`, `core/`,
  `crud/`, `models/`, `database/`, `middleware/`, `utils/`).
- **SQLAlchemy 2 + Alembic** migrations on **Postgres** (auto-create tables in
  dev, migrations in prod).
- **Redis** cache + rate limiting.
- **JWT auth** (sign in / sign up) + **Casbin RBAC** (users, roles, permissions).
- **File storage** (MinIO / S3 / GCS).
- **i18n** (English + French) and request-scoped translation middleware.
- **Login & operation logs**, request tracing (correlation id).
- **Realtime** via python-socketio.
- **Opt-in observability** (`{{cli}} up --monitoring`): Prometheus, Grafana,
  Tempo, Loki.
- **Docker**: multi-stage slim image built with [uv], hot-reload in dev.

## Project structure

```
backend/
├── app/            # Feature sub-apps (admin: auth, users, roles, RBAC, logs)
│   └── admin/
│       ├── api/        # API route handlers
│       ├── schema/     # Pydantic request/response models
│       └── service/    # Business logic
├── common/         # Cross-cutting: security, exceptions, responses, socketio…
├── core/           # Settings (conf.py), app registrar, paths
├── crud/           # Reusable async CRUD over the models
├── database/       # Postgres + Redis connections
├── middleware/     # Access log, i18n, operation log, state
├── models/         # SQLAlchemy models
├── lang/           # i18n message catalogs (en, fr)
├── seeder/         # Database seeds (incl. an example admin)
├── utils/          # Helpers (timezone, encrypt, serializers, health…)
├── cli.py          # In-container commands (used by `{{cli}} auth init`)
└── main.py         # Application entry point
devops/             # Compose helpers / infra
etc/                # Monitoring configs (only when generated with monitoring)
Dockerfile
docker-compose.yml
docker-compose.override.yml      # dev: bind-mount + hot-reload
docker-compose.monitoring.yml    # opt-in observability stack
docker-run.sh                    # shell runner (Unix); `{{cli}}` is the cross-platform equivalent
.env.template                    # copied to .env on first run
pyproject.toml / uv.lock         # dependencies, managed with uv
```

## Configuration

On first `{{cli}} up`, a `.env` is created from `.env.template`. Every value has
a sane default in `backend/core/conf.py`, so you only override what differs.
When running under Docker Compose, the database/Redis/MinIO hosts are pointed
at the container service names automatically.

Common variables:

| Variable | Purpose |
| --- | --- |
| `ENVIRONMENT` | `dev`, `preprod` or `prod`. |
| `POSTGRES_*` | Postgres host, port, user, password, database. |
| `REDIS_*` | Redis host, port, password, database index. |
| `MINIO_*` | Object storage endpoint, keys, bucket. |
| `TOKEN_SECRET_KEY` | Secret used to sign JWT access tokens. |
| `SMTP_*` / `EMAILS_FROM_*` | Outgoing mail. |
| `OBSERVABILITY_ENABLED` / `OTLP_GRPC_ENDPOINT` | Opt-in tracing/metrics export. |

## Database migrations

```bash
{{cli}} db generate --message "add posts table"   # autogenerate from model changes
{{cli}} db preview                                 # inspect the SQL first
{{cli}} db apply                                   # apply (alembic upgrade head)
{{cli}} db pending                                 # current revision vs. head
```

## Authentication

`{{cli}} auth init` creates the first admin user (with the `admin` role) inside
the running API container; you then log in from Swagger at
`/admin/api/v1/docs`. No admin is seeded by default — create yours with
`{{cli}} auth init`.

## License

MIT
