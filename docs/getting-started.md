# Getting started

## What is shaapi?

`shaapi` is a CLI that scaffolds a **lean, production-shaped FastAPI backend** in
seconds — the way `django-admin startproject` does for Django. You get a clean,
layered project with auth, database, migrations, RBAC, file storage and a
one-command Docker workflow, so you can start building features instead of
wiring infrastructure.

## Requirements

- Python ≥ 3.11
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose (for the
  one-command workflow)

## Install

```bash
pip install shaapi
```

## Create a project

```bash
shaapi new "my api"
```

You'll be asked a couple of questions:

```
shaapi creating project my_api
? Include monitoring (Prometheus/Grafana/Tempo/Loki)?  No
? Initialize a git repository?                          Yes
```

Skip the prompts with `-y`, or set everything explicitly:

```bash
shaapi new "my api" -y                 # accept defaults
shaapi new "my api" --monitoring --no-git
shaapi new "my api" --path ./projects
```

The project name is turned into a safe slug (`my api` → `my_api`) used for the
folder, the Docker containers, the database and the app title.

## Run it

```bash
cd my_api
shaapi up                # build + start everything (cross-platform, no bash)
```

> `shaapi` wraps `docker compose` directly, so the same commands work on
> **Windows, macOS and Linux**. On Unix you can also use the bundled
> `./docker-run.sh` shell script — it drives the same stack.

That builds the API image and starts everything (API, Postgres, Redis, MinIO):

- API → http://localhost:8000
- Health → http://localhost:8000/health
- Swagger → http://localhost:8000/admin/api/v1/docs
- ReDoc → http://localhost:8000/admin/api/v1/redocs

In development the source is **bind-mounted with hot-reload** — edit your code
and the server reloads instantly, no rebuild needed.

Once the stack is up, create an admin user (to log into Swagger) and the
storage bucket:

```bash
shaapi auth init         # interactive: email + password
shaapi storage init      # create the MinIO/S3 bucket
```

## Everyday commands

```bash
shaapi up                          # start (build if needed)
shaapi up --monitoring             # + Prometheus/Grafana/Tempo/Loki
shaapi logs                        # tail all logs
shaapi logs api                    # tail API logs only
shaapi restart api                 # restart just the API
shaapi shell                       # shell inside the API container
shaapi db shell                    # psql into Postgres
shaapi db apply                    # alembic upgrade head
shaapi db generate --message "msg" # generate a migration
shaapi down                        # stop everything
```

## Configuration

Everything is configured through `.env` (created automatically from
`.env.template` on first run). Every value has a sane default in
`backend/core/conf.py`, so the app boots out of the box — you only override what
differs. **Change the secrets before going to production.**

## Next steps

- [Architecture](architecture.md) — how the project is organized
- [Create a feature](create-a-feature.md) — build a Todo API in minutes
- [Deployment](deployment.md) — ship it to production
