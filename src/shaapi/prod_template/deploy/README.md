# Deploying to a VPS

This `prod` branch carries the production config. The application code is
identical to `dev` — only the config diverges. Bring code forward by merging
`dev` into `prod`; never edit `backend/` only here.

## One-time server setup

```bash
# 1. Install Docker on the server
ssh root@your-vps 'bash -s' < deploy/provision.sh

# 2. Lock down the firewall (deny inbound except SSH + 80/443)
ssh root@your-vps 'bash -s' < deploy/harden-os.sh
```

## Each deploy

```bash
# On the server, from the project directory (this prod branch):
git pull                       # or push from CI

cp .env.prod.example .env      # first time only
{{cli}} ops secrets --write    # generate + inject real secrets into .env
#   ... then set POSTGRES_PASSWORD / MINIO_SECRET_KEY etc. as needed

{{cli}} up --prod              # base + docker-compose.prod.yml (datastores NOT exposed)
{{cli}} db apply               # run migrations
{{cli}} auth init              # create the first admin
```

Put a reverse proxy (nginx / Caddy / Traefik) in front, terminating TLS on
443 and forwarding to the API on `127.0.0.1:8000`.

## Verify it's hardened

```bash
{{cli}} ops checklist          # the full go-live checklist
ss -tulnp | grep -E ':(5432|9000)'   # should show nothing on 0.0.0.0
```
