# shaapi

**Scaffold lean, batteries-included FastAPI backends — like `django-admin`, for FastAPI.**

Beginners shouldn't have to architect a production backend from scratch. `shaapi`
gives you a clean, opinionated FastAPI project — async SQLAlchemy + Alembic,
Postgres, Redis, JWT auth, Casbin RBAC, file storage, and a one-command Docker
workflow — generated in seconds.

```bash
pip install shaapi
shaapi create-project "my api"
cd my_api
./docker-run.sh up
```

→ API live at `http://localhost:8000`, Swagger at `http://localhost:8000/admin/api/v1/docs`.

## What you get

- **FastAPI** (async) with a clean layered architecture (`app/`, `common/`, `core/`, `crud/`, `models/`, `schemas/`)
- **SQLAlchemy 2 + Alembic** migrations, **Postgres** (auto-create in dev, migrations in prod)
- **Redis** cache + rate limiting
- **JWT auth** + **Casbin RBAC** (users, roles, permissions)
- **File storage** (MinIO / S3 / GCS)
- **Docker**: multi-stage slim image built with [uv], hot-reload in dev (source bind-mount), `docker-run.sh` orchestration
- **Opt-in observability** (`--monitoring`): Prometheus, Grafana, Tempo, Loki

## CLI

```bash
shaapi create-project "my api"          # interactive
shaapi create-project "my api" -y       # accept defaults
shaapi create-project "my api" --monitoring --no-git
shaapi --version
```

## In your generated project

```bash
./docker-run.sh up            # build + start everything (dev: hot-reload)
./docker-run.sh up --monitoring
./docker-run.sh logs          # tail logs
./docker-run.sh migrate       # alembic upgrade head
./docker-run.sh makemigrations "add posts table"
./docker-run.sh down
```

## Documentation

📖 **Full documentation site (EN/FR): https://shalom-302.github.io/shaapi/**

Highlights:
- [Getting started](https://shalom-302.github.io/shaapi/getting-started/)
- [Learn FastAPI with shaapi](https://shalom-302.github.io/shaapi/learn-fastapi/)
- [Architecture](https://shalom-302.github.io/shaapi/architecture/)
- [Build a feature](https://shalom-302.github.io/shaapi/create-a-feature/)
- [Why Docker?](https://shalom-302.github.io/shaapi/why-docker/)
- [Deployment](https://shalom-302.github.io/shaapi/deployment/)

The Markdown sources live in [`docs/`](docs/) (English `*.md`, French `*.fr.md`).

## Example

[`examples/todolist`](examples/todolist) — a complete authenticated Todo API
(JWT, per-user ownership, admin-only endpoint) built on top of shaapi in 5 files.

## Status

Alpha. See the repo for roadmap and contribution guidelines.

## License

MIT

[uv]: https://github.com/astral-sh/uv
