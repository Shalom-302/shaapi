---
title: shaapi
hide:
  - navigation
---

# shaapi

**Scaffold lean, batteries-included FastAPI backends — like `django-admin`, for FastAPI.**

shaapi gives you a clean, production-shaped FastAPI project in seconds: async
SQLAlchemy + Alembic, PostgreSQL, Redis, JWT auth, Casbin RBAC, file storage and
a cross-platform `shaapi` CLI that wraps docker compose. Stop wiring
infrastructure — start building features.

<div class="grid cards" markdown>

-   :material-rocket-launch: **Instant start**

    ---

    `pip install shaapi` → `shaapi new` → `shaapi up` → a working API in under a minute.

-   :material-layers-triple: **Clean architecture**

    ---

    Models · schemas · CRUD · services · routers. The same layering used in
    serious production codebases — ready to learn from.

-   :material-docker: **Docker-first**

    ---

    Multi-stage slim image, hot-reload in dev, migrations in prod, driven by
    the cross-platform `shaapi` CLI (Windows/macOS/Linux, no bash).

-   :material-school: **Learn by reading**

    ---

    A real, well-organized backend. Students learn FastAPI *the production way*
    by exploring a project that actually runs.

</div>

## Quick start

```bash
pip install shaapi
shaapi new "my api"
cd my_api
shaapi up
```

Then optionally create an admin user with `shaapi auth init`.

→ API at **http://localhost:8000** · Swagger at **http://localhost:8000/admin/api/v1/docs**

## What's inside

- **FastAPI** (async) with a layered architecture
- **SQLAlchemy 2 + Alembic** — auto-create in dev, migrations in prod
- **PostgreSQL + Redis** (cache & rate limiting)
- **JWT auth + Casbin RBAC** — users, roles, permissions
- **File storage** — MinIO / S3 / GCS
- **Docker** — slim multi-stage image built with [uv], hot-reload, driven by the cross-platform `shaapi` CLI (`./docker-run.sh` remains as an optional Unix shell alternative)
- **Opt-in observability** — Prometheus, Grafana, Tempo, Loki

Built on the latest stack: **SQLAlchemy 2.0** · **Pydantic v2** · **FastAPI**.

## Where to next?

<div class="grid cards" markdown>

-   [:material-flag-checkered: **Getting started**](getting-started.md)

    Install, create a project, run it.

-   [:material-school: **Learn FastAPI with shaapi**](learn-fastapi.md)

    Understand the architecture — and why it scales.

-   [:material-sitemap: **Architecture**](architecture.md)

    The layers, the lifespan, the config.

-   [:material-puzzle: **Build a feature**](create-a-feature.md)

    A full authenticated Todo API, step by step.

-   [:material-docker: **Why Docker?**](why-docker.md)

    What it buys you, and how to scale up.

-   [:material-cloud-upload: **Deploy**](deployment.md)

    Ship to production on a VPS with TLS.

</div>

---

shaapi is open source (MIT) — [GitHub](https://github.com/Shalom-302/shaapi) ·
[PyPI](https://pypi.org/project/shaapi/)

[uv]: https://github.com/astral-sh/uv
