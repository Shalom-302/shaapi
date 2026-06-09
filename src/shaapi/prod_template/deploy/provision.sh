#!/usr/bin/env bash
# Provision a fresh Ubuntu/Debian VPS for {{cli}}: install Docker Engine +
# the compose plugin. Run as root (or with sudo) ON THE SERVER.
#
#   ssh root@your-vps 'bash -s' < deploy/provision.sh
#
set -euo pipefail

echo ">> Installing Docker Engine + compose plugin..."
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker
docker --version
echo ">> Docker ready. Next: bash deploy/harden-os.sh"
