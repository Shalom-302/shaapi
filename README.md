# shaapi

[![PyPI version](https://img.shields.io/pypi/v/shaapi?color=teal)](https://pypi.org/project/shaapi/)
[![Python](https://img.shields.io/pypi/pyversions/shaapi)](https://pypi.org/project/shaapi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://shalom-302.github.io/shaapi/)
[![Publish to PyPI](https://github.com/Shalom-302/shaapi/actions/workflows/publish.yml/badge.svg)](https://github.com/Shalom-302/shaapi/actions/workflows/publish.yml)
[![Deploy docs](https://github.com/Shalom-302/shaapi/actions/workflows/docs.yml/badge.svg)](https://github.com/Shalom-302/shaapi/actions/workflows/docs.yml)
[![Built with FastAPI](https://img.shields.io/badge/built%20with-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

**Scaffold lean, batteries-included FastAPI backends — like `django-admin`, for FastAPI.**

Beginners shouldn't have to architect a production backend from scratch. `shaapi`
gives you a clean, opinionated FastAPI project — async SQLAlchemy + Alembic,
Postgres, Redis, JWT auth, Casbin RBAC, file storage, and a one-command Docker
workflow — generated in seconds.

```bash
pip install shaapi
shaapi new "my api"
cd my_api
shaapi up
```

→ API live at `http://localhost:8000`, Swagger at `http://localhost:8000/admin/api/v1/docs`.

## What you get

- **FastAPI** (async) with a clean layered architecture (`app/`, `common/`, `core/`, `crud/`, `models/`, `schemas/`)
- **SQLAlchemy 2 + Alembic** migrations, **Postgres** (auto-create in dev, migrations in prod)
- **Redis** cache + rate limiting
- **JWT auth** + **Casbin RBAC** (users, roles, permissions)
- **File storage** (MinIO / S3 / GCS)
- **Docker**: multi-stage slim image built with [uv], hot-reload in dev (source bind-mount), cross-platform `shaapi` orchestration (no bash)
- **Opt-in observability** (`--monitoring`): Prometheus, Grafana, Tempo, Loki
- **Production tooling** (`shaapi ops`): hardened compose overlay (datastores off the public network), secret generation, VPS provisioning/firewall scripts, and a `dev`/`prod` git-branch split (same code, config-only divergence)
- **Security testing** (`shaapi sec`): static audit + black-box probes (default-secret JWT forge, auth, login rate-limit, exposed ports), with a CI-friendly exit code

> Generated projects are **secure by default**: a production fail-fast guard refuses to boot with default secrets, the container runs non-root, and the datastores are never exposed in production.

## CLI

```bash
shaapi new "my api"                       # interactive scaffold
shaapi new "my api" -y                    # accept defaults
shaapi new "my api" --prod                # + production config on a `prod` git branch
shaapi up / db apply / auth init          # run the stack (cross-platform docker wrapper)
shaapi ops harden / secrets / checklist   # production hardening (shaops)
shaapi sec audit / auth / scan / ports    # security testing (shasec)
shaapi --version
```

## In your generated project

```bash
shaapi up                       # build + start everything (dev: hot-reload)
shaapi up --prod                # production: datastores not exposed
shaapi db apply                 # alembic upgrade head
shaapi db generate -m "add posts table"
shaapi auth init                # create the first admin
shaapi logs / shaapi down
```

> On Linux/macOS a bundled `./docker-run.sh` offers the same commands if you
> prefer a plain shell script.

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
