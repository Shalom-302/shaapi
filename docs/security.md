# Security (shasec)

`shaapi sec` — **shasec** — audits a shaapi project and **attacks a running API**
to confirm it resists. It's pure standard library (no extra dependency) and
black-box, so you can point it at any HTTP API, not just shaapi.

Every check produces a **severity**; the command **exits non-zero on any
HIGH/CRITICAL**, so you can drop it into CI as a gate.

## Static audit — `shaapi sec audit`

Run it inside a project. It codifies the security review of the generated code:

| Check | Severity |
| --- | --- |
| Default secrets still in `.env` (`TOKEN_SECRET_KEY`, `POSTGRES_PASSWORD`, …) | CRITICAL |
| `.env` tracked by git | CRITICAL |
| Committed credentials in `seeder/json/*` | HIGH |
| Base compose publishes datastore ports | HIGH |
| CORS `*` with credentials | HIGH |
| Container runs as root | MEDIUM |
| Weak cookie flags | MEDIUM |
| API docs not gated by environment | MEDIUM |
| External geo-IP enabled | LOW |
| Production fail-fast guard present | PASS |

```bash
shaapi sec audit
```

On a fresh project this flags only the **dev default secrets** (fine for dev,
fatal for prod — the guard blocks them). After `shaapi ops secrets --write`,
it's clean.

## Dynamic probes — against a running API

### `shaapi sec auth <url>`

Black-box authentication attacks:

- **Default-secret JWT forge** — signs a token with the public default
  `TOKEN_SECRET_KEY` and calls `/auth/me`. A stateless API that trusts the
  signature alone would return `200`; **shaapi rejects it** (`401`) because
  tokens are also tracked server-side in Redis.
- **Unprotected routes** — protected endpoints hit without a token must not
  return `200`.
- **Login rate-limiting** — rapid attempts must eventually be throttled (`429`).

```bash
shaapi sec auth http://localhost:8000/admin/api/v1
```

### `shaapi sec scan <url>`

Reports missing security headers (HSTS, X-Content-Type-Options, X-Frame-Options,
CSP) and the size of the exposed OpenAPI surface.

### `shaapi sec ports <host>`

TCP-connects to the datastore ports (5432 / 6379 / 9000 / 9001). They should be
**open in dev** (convenience) and **closed under `--prod`**.

```bash
shaapi sec ports localhost     # dev: Postgres/MinIO open
shaapi sec ports your-vps      # prod: must be closed
```

## In CI

```bash
shaapi sec audit || exit 1     # fails the build on HIGH/CRITICAL
```

## The philosophy

shaapi is built to **resist shasec**: a forged default-secret token is rejected,
the login is throttled, protected routes require auth, and production closes the
datastores. shasec is how you *prove* it — on both your `dev` and `prod`
branches. See [Production (shaops)](production.md).
