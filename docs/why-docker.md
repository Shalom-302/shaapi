# Why Docker?

shaapi is Docker-first. Here's the *why* — useful whether you're learning or
evaluating it for a serious project.

## The problem Docker solves

A backend isn't just Python. It needs PostgreSQL, Redis, object storage, the
right system libraries, the right Python version… Without Docker, every developer
(and every server) must install and match all of that by hand. The result is the
classic *"works on my machine"*.

With shaapi, the entire stack is described in code:

```bash
shaapi up
```

One command gives **every** developer — and production — the *same* API,
database, cache and storage. New contributor onboarding goes from a day to a
minute.

## What you get

- **Reproducibility** — `uv.lock` pins exact dependency versions; the image is
  byte-for-byte rebuildable.
- **Dev/prod parity** — the same image runs locally and in production.
- **Isolation** — no global installs polluting your machine.
- **Batteries included** — Postgres, Redis and MinIO start alongside the API,
  pre-wired.

## How shaapi uses Docker

### A slim, multi-stage image
The `Dockerfile` builds in two stages:

1. **builder** — installs dependencies with [uv] into an isolated virtualenv.
2. **runtime** — a minimal `python:3.11-slim` image that copies only the built
   venv and the app. No build tools ship to production → a smaller, safer image.

### Dev and prod, same image, different behavior

| | Dev (default) | Prod (`--prod`) |
|---|---|---|
| Source code | **bind-mounted** (`.:/app`) | baked into the image |
| Reload | yes (`uvicorn --reload`) | no |
| Schema | auto-created | Alembic migrations |

In development the source is mounted into the running container, so editing a
file **hot-reloads** the server instantly — no rebuild. (shaapi keeps the
virtualenv at `/opt/venv`, *outside* the mounted `/app`, so the mount never
shadows your dependencies — a subtle but important detail.)

In production you build once and serve the baked code, with migrations applied
on startup.

### `docker-compose`, explained
The base `docker-compose.yml` declares the services and how they connect:

- `api` — your FastAPI app
- `postgres`, `redis`, `minio` — with **healthchecks**, so the API only starts
  once its dependencies are actually ready
- a private network so services talk to each other by name

`docker-compose.override.yml` adds the dev bind-mount automatically;
`docker-compose.monitoring.yml` adds the optional observability stack.

`shaapi` is the cross-platform wrapper over all of that — it drives `docker
compose` directly and works on Windows, macOS and Linux, no bash required:

```bash
shaapi up | down | logs | restart api | shell | db shell | redis
shaapi db apply | db generate --message "msg"
shaapi up --monitoring                 # + Prometheus/Grafana/Tempo/Loki
shaapi up --prod                       # production mode
```

`./docker-run.sh` is the equivalent shell script for Unix users who prefer it.

## Can I use this for a big project?

Absolutely — the Docker setup is designed to grow:

- **Scale the API** — run multiple `api` workers behind a load balancer / reverse
  proxy. The image is stateless.
- **Externalize state** — point `POSTGRES_HOST` / `REDIS_HOST` at managed
  services (RDS, ElastiCache…) instead of the bundled containers.
- **Background jobs** — add a Celery worker service reusing the same image.
- **Observability** — `--monitoring` brings metrics, traces and logs for when you
  need to debug under load.
- **CI/CD** — the reproducible build slots straight into any pipeline.

The same `shaapi up` that a student runs on their laptop is the foundation
a team runs in production. That's the point.

See [Deployment](deployment.md) for a concrete VPS + TLS walkthrough.

[uv]: https://github.com/astral-sh/uv
