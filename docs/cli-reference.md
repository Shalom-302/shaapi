# CLI reference

`shaapi` is two tools in one:

- a **scaffolder** — `shaapi new "my api"` generates a project;
- a **project runner** — from inside a generated project, `shaapi up`,
  `shaapi db apply`, `shaapi auth init`… wrap `docker compose` **directly**, so
  the same commands work on **Windows, macOS and Linux** (no bash, no
  `./docker-run.sh` "is not recognized").

```bash
pip install shaapi
shaapi --help          # list every command
shaapi <group> --help  # e.g. shaapi db --help
```

## Conventions

- **`--path, -p`** — almost every runner command accepts `-p <dir>` to target a
  project directory. It defaults to `.`, and shaapi walks up to find the project
  root (the folder with `backend/` + `pyproject.toml`), so you can run commands
  from any subfolder.
- **Stack must be running** — `db`, `auth`, `storage` and `shell` commands
  `exec` into a container. If the stack is down they fail fast with
  *"Start the stack first with `shaapi up`"* instead of a cryptic Docker error.
- **Global flags** — `shaapi --version` (`-V`) prints the version; `--help` is
  available on every command and group.

---

## Scaffolding

### `shaapi new`

Create a new project.

```bash
shaapi new "my api"
shaapi new "my api" -y                      # accept defaults, no prompts
shaapi new "my api" --monitoring --no-git
shaapi new "my api" --path ./projects
```

| Option | Description |
| --- | --- |
| `--path, -p` | Where to create the project (default `.`). |
| `--monitoring / --no-monitoring` | Include the Prometheus/Grafana/Tempo/Loki stack. |
| `--git / --no-git` | Initialize a git repository. |
| `--yes, -y` | Accept defaults, skip the interactive prompts. |

The project name becomes a safe slug (`my api` → `my_api`) used for the folder,
the Docker containers, the database and the app title.

!!! note "Alias"
    `shaapi create-project` is a hidden, deprecated alias of `shaapi new`.

---

## Lifecycle

### `shaapi up`

Build and start the whole stack (API, Postgres, Redis, MinIO). Dev mode
bind-mounts the source for hot-reload.

```bash
shaapi up
shaapi up --monitoring     # + Prometheus/Grafana/Tempo/Loki
shaapi up --prod           # production: no bind-mount, serve the baked image
```

| Option | Description |
| --- | --- |
| `--monitoring` | Add the observability stack (requires a project generated with monitoring). |
| `--prod` | Production mode — no dev bind-mount. |
| `--path, -p` | Project directory. |

### `shaapi down`

Stop and remove the stack's containers.

```bash
shaapi down
shaapi down --monitoring   # also stop the monitoring stack
```

### `shaapi logs`

Tail container logs (Ctrl-C to stop).

```bash
shaapi logs        # all services
shaapi logs api    # one service
```

### `shaapi restart`

Restart all containers, or a single service.

```bash
shaapi restart
shaapi restart api
```

### `shaapi ps`

Show container status.

### `shaapi shell`

Open a `bash` shell inside the `api` container.

### `shaapi redis`

Open `redis-cli` inside the Redis container.

---

## Database (`db`)

Migrations are powered by Alembic and run inside the `api` container.

### `shaapi db generate`

Autogenerate a migration from your model changes.

```bash
shaapi db generate --message "add posts table"
shaapi db generate -m "add posts table"
```

| Option | Description |
| --- | --- |
| `--message, -m` | Migration message (**required**). |
| `--path, -p` | Project directory. |

!!! tip "New models are auto-detected"
    Drop a `backend/models/<name>.py` defining a `Base` subclass and it's picked
    up automatically — you no longer edit `backend/models/__init__.py`.

### `shaapi db apply`

Apply pending migrations (`alembic upgrade head`).

### `shaapi db preview`

Print the SQL that `shaapi db apply` would run, **without executing it**.

### `shaapi db pending`

Show the current database revision versus the latest head (a mismatch means
migrations are pending).

### `shaapi db shell`

Open `psql` inside the Postgres container (user/database read from `.env`).

---

## Auth (`auth`)

### `shaapi auth init`

Create an admin user (with the `admin` role) so you can log into Swagger. Prompts
for email and password if not provided.

```bash
shaapi auth init
shaapi auth init --email you@example.com --password "s3cret"
```

| Option | Description |
| --- | --- |
| `--email, -e` | Admin email (login). Prompted if omitted. |
| `--password, -w` | Admin password. Prompted (hidden) if omitted. |
| `--path, -p` | Project directory. |

---

## Storage (`storage`)

### `shaapi storage init`

Ensure the configured object-storage bucket (MinIO / S3) exists.

```bash
shaapi storage init
```

---

## Plugins

### `shaapi list-plugins`

List the plugins you can add to a project.

### `shaapi add`

Add a plugin to the current project — copies it into `backend/plugins/<name>/`,
injects its Python dependencies into `pyproject.toml` and refreshes `uv.lock`.

```bash
shaapi add payment
```

Reload the API afterwards with `shaapi restart api`.

### `shaapi remove`

Remove an installed plugin.

```bash
shaapi remove payment
```

---

## Meta

### `shaapi version`

Print the installed shaapi version (same as `shaapi --version`).

---

## `docker-run.sh` equivalence

On Linux/macOS the bundled `./docker-run.sh` shell script drives the same stack
if you prefer a plain script. Mapping:

| `shaapi` | `./docker-run.sh` |
| --- | --- |
| `shaapi up` | `./docker-run.sh up` |
| `shaapi up --monitoring` | `./docker-run.sh up --monitoring` |
| `shaapi up --prod` | `./docker-run.sh up --prod` |
| `shaapi down` | `./docker-run.sh down` |
| `shaapi logs` | `./docker-run.sh logs` |
| `shaapi logs api` | `./docker-run.sh api-logs` |
| `shaapi restart api` | `./docker-run.sh restart-api` |
| `shaapi shell` | `./docker-run.sh shell` |
| `shaapi db shell` | `./docker-run.sh db` |
| `shaapi redis` | `./docker-run.sh redis` |
| `shaapi db apply` | `./docker-run.sh migrate` |
| `shaapi db generate -m "msg"` | `./docker-run.sh makemigrations "msg"` |

`shaapi` is the cross-platform default; `./docker-run.sh` is the Unix-only
equivalent.
