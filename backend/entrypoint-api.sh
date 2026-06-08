#!/bin/bash
set -e

# Locale (matches the Dockerfile)
export LANG=fr_FR.UTF-8
export LANGUAGE=fr_FR.UTF-8
export LC_ALL=fr_FR.UTF-8

cd backend

# Apply database migrations (idempotent: no-op if already up to date).
# Migrations are authored explicitly with `shaapi makemigrations`, never
# auto-generated at boot.
alembic upgrade head

# Start the API server (exec => uvicorn becomes PID 1 and receives signals)
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
