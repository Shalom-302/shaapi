# Deployment

shaapi ships a dev-first workflow (source bind-mount + hot-reload) and a
production mode (baked image, no mount). This guide takes you to a running
production deployment on a VPS.

## Dev vs prod, in one picture

| | Dev (default) | Prod (`--prod`) |
|---|---|---|
| Source | bind-mounted (`.:/app`) | baked into the image |
| Reload | yes (`--reload`) | no |
| Schema | auto-created (`DB_AUTO_CREATE=true`) | Alembic migrations |
| Command | `./docker-run.sh up` | `./docker-run.sh up --prod` |

## 1. Production checklist

Before deploying, edit `.env`:

```env
ENVIRONMENT=prod
DB_AUTO_CREATE=false

# Strong, unique secrets — never the dev defaults
TOKEN_SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(32))">
OPERA_LOG_ENCRYPT_SECRET_KEY=<python -c "import os;print(os.urandom(32).hex())">

# Real database / redis / storage credentials
POSTGRES_PASSWORD=<strong-password>
MINIO_ACCESS_KEY=<key>
MINIO_SECRET_KEY=<secret>

# Your front-end origin(s) for CORS — set in backend/core/conf.py or env
```

Make sure you have an initial migration committed and your schema is captured:

```bash
./docker-run.sh makemigrations "initial"   # if you added models
```

## 2. Provision a VPS

Any Linux box with Docker works (Ubuntu shown):

```bash
# On the server
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # re-login afterwards
git clone <your-project-repo> my_api && cd my_api
cp .env.template .env && nano .env      # apply the checklist above
```

## 3. Start in production mode

```bash
./docker-run.sh up --prod
```

This builds the slim image and runs the stack **without** the dev bind-mount,
serving the baked code. The entrypoint runs `alembic upgrade head` on start, so
your schema is migrated automatically.

Useful prod commands:

```bash
./docker-run.sh logs --prod
./docker-run.sh migrate --prod
./docker-run.sh down --prod
```

## 4. TLS / reverse proxy

Run a reverse proxy in front of the API on port 8000 to terminate HTTPS. With
[Caddy](https://caddyserver.com) it's a two-line `Caddyfile`:

```
api.example.com {
    reverse_proxy localhost:8000
}
```

Caddy fetches and renews Let's Encrypt certificates automatically. Traefik or
nginx work just as well.

## 5. Observability (optional)

```bash
./docker-run.sh up --prod --monitoring
```

Adds Prometheus, Tempo, Loki and Grafana, and rebuilds the API image with the
monitoring extra and `OBSERVABILITY_ENABLED=true`.

- Grafana → `http://<host>:3000`
- Prometheus → `http://<host>:9090`

Keep these ports firewalled / behind auth in production.

## 6. Database backups

The simplest approach is a scheduled `pg_dump`:

```bash
# crontab -e  → daily at 02:00
0 2 * * * docker compose -f /path/my_api/docker-compose.yml exec -T postgres \
  pg_dump -U postgres shaapi | gzip > /backups/db-$(date +\%F).sql.gz
```

For automated, rotated backups, add a `prodrigestivill/postgres-backup-local`
service to your compose file.

## 7. Updating

```bash
git pull
./docker-run.sh up --prod        # rebuilds only if deps/code changed
```

Because dependencies are pinned in `uv.lock`, builds are reproducible.

---

That's it — a reproducible, migration-driven, TLS-terminated deployment. Pair it
with the [architecture](architecture.md) overview to harden further (workers,
external Postgres/Redis, secrets manager).
