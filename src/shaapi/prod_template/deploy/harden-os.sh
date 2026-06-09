#!/usr/bin/env bash
# Harden a VPS firewall for {{cli}}: deny all inbound except SSH and web.
# Run as root (or sudo) ON THE SERVER. Review before running — it changes your
# firewall, and a wrong SSH port here can lock you out.
set -euo pipefail

SSH_PORT="${SSH_PORT:-22}"

echo ">> Configuring UFW (deny incoming, allow SSH + HTTP/HTTPS)..."
ufw default deny incoming
ufw default allow outgoing
ufw allow "${SSH_PORT}"/tcp     # SSH
ufw allow 80,443/tcp            # web traffic (reverse proxy in front of the API)
ufw --force enable
ufw status verbose

echo ""
echo ">> Verifying the datastores are NOT listening on a public interface"
echo "   (expect NO 0.0.0.0 lines for 5432 / 9000 / 9001):"
if ss -tulnp | grep -E '0\.0\.0\.0:(5432|9000|9001)\b'; then
  echo "   !! WARNING: a datastore is publicly bound. Did you start with --prod?"
  exit 1
else
  echo "   OK — Postgres/Redis/MinIO are internal-only."
fi
