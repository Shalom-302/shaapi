# Production (shaops)

`shaapi ops` — **shaops** — turns the manual "ship it to a VPS" runbook into a
few commands. It only **generates files you run yourself** on the server; it
never connects out and never handles your credentials over the wire.

## Secure by default

A generated project is hard to deploy *insecurely*:

- a **production fail-fast guard** refuses to boot (outside dev) while any
  development default secret remains;
- the container runs as a **non-root** user;
- in production the **datastores publish no host ports** — Postgres, Redis and
  MinIO are reachable only on the internal Docker network.

## The dev / prod branch model

```bash
shaapi new "my api" --prod
```

This scaffolds a git repository with two branches:

| Branch | Contents |
| --- | --- |
| `dev` | the lean development project (you start here) |
| `prod` | the same project **plus** the production config |

The **application code (`backend/`) is identical on both branches** — only the
config diverges (the prod compose overlay, env example, deploy scripts). You
ship by merging `dev` into `prod`; the VPS tracks `prod`. No code drift.

> Already have a project? Run `shaapi ops harden` to add the production config
> in place.

## What `shaapi ops harden` writes

| File | Role |
| --- | --- |
| `docker-compose.prod.yml` | overlay: datastores publish **no host ports**, `ENVIRONMENT=prod`, a daily Postgres backup sidecar |
| `.env.prod.example` | the production env template (copy to `.env` on the server) |
| `deploy/provision.sh` | install Docker Engine + compose on Ubuntu/Debian |
| `deploy/harden-os.sh` | firewall (ufw: deny inbound except 22/80/443) + a port-exposure check |

## Going live

```bash
# 1. On the server (one-time)
ssh root@your-vps 'bash -s' < deploy/provision.sh    # install Docker
ssh root@your-vps 'bash -s' < deploy/harden-os.sh    # firewall

# 2. Config (on the server)
cp .env.prod.example .env
shaapi ops secrets --write     # generate + inject strong secrets into .env
#   ... then set POSTGRES_PASSWORD / MINIO_SECRET_KEY as needed

# 3. Run the hardened stack
shaapi up --prod               # loads docker-compose.prod.yml (datastores closed)
shaapi db apply                # migrations
shaapi auth init               # first admin
```

Put a reverse proxy (nginx / Caddy / Traefik) in front, terminating TLS on 443
and forwarding to the API on `127.0.0.1:8000`.

`shaapi ops checklist` prints the full go-live checklist at any time.

## Verify the hardening

```bash
shaapi sec ports your-vps      # Postgres/MinIO must be CLOSED
ss -tulnp | grep -E ':(5432|9000)'   # nothing on 0.0.0.0
```

See [Security (shasec)](security.md) to attack your own API and confirm it
resists.
