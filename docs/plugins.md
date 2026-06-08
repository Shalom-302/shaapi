# Plugins

shaapi ships a small core and lets you pull in extra features **only when you
need them** — the opposite of frameworks that load every module at startup.

A plugin is a self-contained blueprint. `shaapi add <name>` copies it into your
project under `backend/plugins/<name>/`; from then on it's *your* code (read it,
edit it). Its router is auto-discovered — **nothing loads unless you add it**, so
your build only contains what you chose.

## Commands

```bash
shaapi list-plugins          # see the catalog
shaapi add advanced_auth     # copy a plugin into backend/plugins/
shaapi remove advanced_auth  # remove it
```

`add` also injects any Python dependencies the plugin needs into your
`pyproject.toml` and refreshes `uv.lock`, so it builds out of the box. After
adding, reload the API (`./docker-run.sh restart-api`) or rebuild.

In development the plugin's tables auto-create on startup. For production,
generate a migration: `./docker-run.sh makemigrations "add <plugin>"`.

## Available plugins (v0.2.0)

| Plugin | What it does | Endpoints (under `/admin/api/v1`) |
|---|---|---|
| `webhooks` | Register subscriptions, emit HMAC-signed events to URLs | `/webhooks` |
| `advanced_audit` | Application audit trail (who did what, on what) | `/audit/logs` |
| `advanced_auth` | TOTP multi-factor auth on top of the built-in users | `/auth/mfa` |
| `user_analytics` | Track events, query aggregated stats | `/analytics` |
| `payment` | Payments via a pluggable provider (Stripe included) | `/payments` |

All endpoints are JWT-protected. Each plugin also exposes a service you can call
from your own code (e.g. `audit_service.record(...)`, `webhook_service.emit(...)`).

!!! note "More coming"
    This is a starter set. Tell us which plugins you need next — the catalog grows
    based on what the community actually uses.

## Writing your own plugin

A plugin is just a folder under `backend/plugins/<name>/` that exposes a `router`
in its `router` module — exactly like the [feature you build in the tutorial](create-a-feature.md):

```
backend/plugins/myplugin/
├── __init__.py        # from backend.plugins.myplugin.router import router
├── models.py          # SQLAlchemy models
├── schemas.py         # Pydantic schemas
├── service.py         # business logic
└── router.py          # APIRouter named `router`
```

That's all the auto-discovery needs. Once the folder is there, the API loads it
on the next restart.
